"""SQLite compatible schema for development

Revision ID: 999_dev_sqlite_schema
Revises: 
Create Date: 2025-05-05 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '999_dev_sqlite_schema'
down_revision = '001_add_client_int'
branch_labels = None
depends_on = None


def upgrade():
    # Create a complete development schema for SQLite
    # Organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False)
    )
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(100), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False)
    )
    
    # Clients table
    op.create_table(
        'clients',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('tax_id', sa.String(50), nullable=False),
        sa.Column('email', sa.String(100)),
        sa.Column('phone', sa.String(20)),
        sa.Column('address', sa.String(255)),
        sa.Column('industry', sa.String(50)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('status', sa.String(20), server_default='active', nullable=False)
    )

    # Integrations table
    op.create_table(
        'integrations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('client_id', sa.String(36), sa.ForeignKey('clients.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('updated_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('status', sa.String(20), server_default='active', nullable=False)
    )

    # Integration config history
    op.create_table(
        'integration_config_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('integration_id', sa.String(36), sa.ForeignKey('integrations.id'), nullable=False),
        sa.Column('changed_by', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('previous_config', sa.JSON()),
        sa.Column('new_config', sa.JSON(), nullable=False),
        sa.Column('changed_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('change_reason', sa.String(255))
    )

    # IRN Records table
    op.create_table(
        'irn_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('irn', sa.String(50), nullable=False, unique=True),
        sa.Column('service_id', sa.String(50), nullable=False),
        sa.Column('integration_id', sa.String(36), sa.ForeignKey('integrations.id'), nullable=False),
        sa.Column('timestamp', sa.String(8), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('valid_until', sa.DateTime(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='unused',
                 check_constraint="status IN ('unused', 'active', 'expired', 'revoked', 'invalid')"),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('invoice_id', sa.String(50), nullable=True),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('hash_value', sa.String(128), nullable=True),
        sa.Column('verification_code', sa.String(20), nullable=True),
        sa.Column('issued_by', sa.String(100), nullable=True),
        sa.Column('odoo_invoice_id', sa.Integer(), nullable=True)
    )

    # Validation Rules
    op.create_table(
        'validation_rules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('field_path', sa.String(255), nullable=True),
        sa.Column('validation_logic', sa.JSON(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, server_default='error'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True)
    )

    # Invoice Validation Records
    op.create_table(
        'invoice_validation_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('integration_id', sa.String(36), sa.ForeignKey('integrations.id'), nullable=False),
        sa.Column('irn', sa.String(50), sa.ForeignKey('irn_records.irn'), nullable=True),
        sa.Column('invoice_data', sa.JSON(), nullable=False),
        sa.Column('is_valid', sa.Boolean(), nullable=False),
        sa.Column('validation_time', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('issues', sa.JSON(), nullable=True),
        sa.Column('external_id', sa.String(100), nullable=True)
    )

    # Invoice Data
    op.create_table(
        'invoice_data',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('odoo_invoice_id', sa.Integer(), nullable=False),
        sa.Column('invoice_number', sa.String(50), nullable=False),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('customer_name', sa.String(100), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('currency_code', sa.String(3), nullable=False),
        sa.Column('line_items_hash', sa.String(128), nullable=True),
        sa.Column('line_items_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('odoo_partner_id', sa.Integer(), nullable=True),
        sa.Column('odoo_currency_id', sa.Integer(), nullable=True)
    )

    # IRN Validation Records
    op.create_table(
        'irn_validation_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('irn', sa.String(50), sa.ForeignKey('irn_records.irn'), nullable=False),
        sa.Column('validation_time', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('is_valid', sa.Boolean(), nullable=False),
        sa.Column('validation_message', sa.String(512), nullable=True),
        sa.Column('validated_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('validation_source', sa.String(50), nullable=False, server_default='system'),
        sa.Column('request_data', sa.JSON(), nullable=True),
        sa.Column('response_data', sa.JSON(), nullable=True)
    )


def downgrade():
    # Drop all tables in reverse order
    op.drop_table('irn_validation_records')
    op.drop_table('invoice_data')
    op.drop_table('invoice_validation_records')
    op.drop_table('validation_rules')
    op.drop_table('irn_records')
    op.drop_table('integration_config_history')
    op.drop_table('integrations')
    op.drop_table('clients')
    op.drop_table('users')
    op.drop_table('organizations')
