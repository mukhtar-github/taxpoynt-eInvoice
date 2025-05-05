"""Enhance IRN system for OdooRPC integration

Revision ID: 004_enhance_irn_system
Revises: 003_add_validation_models
Create Date: 2025-05-05 05:00:00.000000

"""
from alembic import op # type: ignore
import sqlalchemy as sa # type: ignore
from sqlalchemy.dialects import postgresql # type: ignore

# revision identifiers, used by Alembic.
revision = '004_enhance_irn_system'
down_revision = '003_add_validation_models'
branch_labels = None
depends_on = None


def upgrade():
    # Make SQLite compatible by checking the database dialect
    import re
    from sqlalchemy import text
    from sqlalchemy.engine import reflection
    
    conn = op.get_bind()
    inspector = reflection.Inspector.from_engine(conn)
    dialect_name = conn.dialect.name
    
    # For SQLite, we'll use the JSON type instead of JSONB
    json_type = "JSON" if dialect_name == "sqlite" else "JSONB"
    
    # 1. Alter irn_records table to add new fields and change status to enum
    
    # First, create the status enum type (only for PostgreSQL)
    if dialect_name == 'postgresql':
        op.execute("""
        CREATE TYPE irn_status AS ENUM ('unused', 'active', 'expired', 'revoked', 'invalid');
        """)
        
        # Update IRN status column to use the enum type
        op.alter_column('irn_records', 'status', 
                       existing_type=sa.String(20),
                       type_=sa.Enum('unused', 'active', 'expired', 'revoked', 'invalid', 
                                   name='irn_status',
                                   native_enum=True),
                       nullable=False,
                       server_default=sa.text("'unused'::irn_status"))
    else:
        # For SQLite, we'll keep using the VARCHAR/TEXT for status
        # SQLite doesn't support ENUM types or complex ALTER statements
        op.execute("PRAGMA foreign_keys=off")
        
        # Create a temporary table with the same structure but status as TEXT
        op.execute("""
        CREATE TEMPORARY TABLE irn_records_backup (
            id TEXT PRIMARY KEY,
            irn TEXT NOT NULL,
            service_id TEXT NOT NULL,
            integration_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            generated_at TIMESTAMP NOT NULL,
            valid_until TIMESTAMP NOT NULL,
            metadata TEXT,
            status TEXT NOT NULL DEFAULT 'unused',
            used_at TIMESTAMP,
            invoice_id TEXT,
            created_by TEXT
        )
        """)
        
        # Copy data from the original table to the backup
        op.execute("""
        INSERT INTO irn_records_backup 
        SELECT id, irn, service_id, integration_id, timestamp, generated_at, valid_until, 
               metadata, status, used_at, invoice_id, created_by
        FROM irn_records
        """)
        
        # Drop the original table
        op.execute("DROP TABLE irn_records")
        
        # Create a new table with the desired structure
        op.execute("""
        CREATE TABLE irn_records (
            id TEXT PRIMARY KEY,
            irn TEXT NOT NULL,
            service_id TEXT NOT NULL,
            integration_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            generated_at TIMESTAMP NOT NULL,
            valid_until TIMESTAMP NOT NULL,
            metadata TEXT,
            status TEXT NOT NULL DEFAULT 'unused',
            used_at TIMESTAMP,
            invoice_id TEXT,
            created_by TEXT,
            CHECK (status IN ('unused', 'active', 'expired', 'revoked', 'invalid'))
        )
        """)
        
        # Copy data back
        op.execute("""
        INSERT INTO irn_records 
        SELECT id, irn, service_id, integration_id, timestamp, generated_at, valid_until, 
               metadata, status, used_at, invoice_id, created_by
        FROM irn_records_backup
        """)
        
        # Drop the backup table
        op.execute("DROP TABLE irn_records_backup")
        op.execute("PRAGMA foreign_keys=on")
    
    # Add new columns to irn_records
    op.add_column('irn_records', sa.Column('hash_value', sa.String(128), nullable=True))
    op.add_column('irn_records', sa.Column('verification_code', sa.String(64), nullable=True))
    op.add_column('irn_records', sa.Column('issued_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True))
    op.add_column('irn_records', sa.Column('odoo_invoice_id', sa.Integer(), nullable=True))
    
    # For existing entries, migrate data from 'metadata' column to 'meta_data'
    op.execute("""
    ALTER TABLE irn_records RENAME COLUMN metadata TO meta_data;
    """)
    
    # 2. Create invoice_data table
    # Make SQLite compatible by replacing JSONB with JSON when using SQLite
    op.create_table(
        'invoice_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('irn', sa.String(50), sa.ForeignKey('irn_records.irn'), nullable=False, unique=True),
        sa.Column('invoice_number', sa.String(50), nullable=False),
        sa.Column('invoice_date', sa.DateTime(), nullable=False),
        sa.Column('customer_name', sa.String(255), nullable=False),
        sa.Column('customer_tax_id', sa.String(50), nullable=True),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('currency_code', sa.String(3), nullable=False),
        sa.Column('line_items_hash', sa.String(128), nullable=True),
        sa.Column('line_items_data', getattr(postgresql, json_type)(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('odoo_partner_id', sa.Integer(), nullable=True),
        sa.Column('odoo_currency_id', sa.Integer(), nullable=True),
    )
    
    # 3. Create irn_validation_records table
    op.create_table(
        'irn_validation_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('irn', sa.String(50), sa.ForeignKey('irn_records.irn'), nullable=False),
        sa.Column('validation_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('validation_status', sa.Boolean(), nullable=False),
        sa.Column('validation_message', sa.String(512), nullable=True),
        sa.Column('validated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('validation_source', sa.String(50), nullable=False, server_default='system'),
        sa.Column('request_data', getattr(postgresql, json_type)(astext_type=sa.Text()), nullable=True),
        sa.Column('response_data', getattr(postgresql, json_type)(astext_type=sa.Text()), nullable=True),
    )
    
    # Add indexes for better performance
    op.create_index('idx_invoice_data_irn', 'invoice_data', ['irn'])
    op.create_index('idx_validation_records_irn', 'irn_validation_records', ['irn'])
    op.create_index('idx_validation_date', 'irn_validation_records', ['validation_date'])
    op.create_index('idx_irn_odoo_invoice_id', 'irn_records', ['odoo_invoice_id'])


def downgrade():
    # Drop indexes first
    op.drop_index('idx_irn_odoo_invoice_id', table_name='irn_records')
    op.drop_index('idx_validation_date', table_name='irn_validation_records')
    op.drop_index('idx_validation_records_irn', table_name='irn_validation_records')
    op.drop_index('idx_invoice_data_irn', table_name='invoice_data')
    
    # Drop tables
    op.drop_table('irn_validation_records')
    op.drop_table('invoice_data')
    
    # Revert irn_records changes
    # First create a temporary string column
    op.add_column('irn_records', sa.Column('status_str', sa.String(20), nullable=True))
    
    # Copy data from enum to string
    op.execute("""
    UPDATE irn_records SET status_str = status::text;
    """)
    
    # Drop enum column and rename string column
    op.drop_column('irn_records', 'status')
    op.alter_column('irn_records', 'status_str', new_column_name='status', nullable=False, server_default='unused')
    
    # Drop other columns added
    op.drop_column('irn_records', 'odoo_invoice_id')
    op.drop_column('irn_records', 'issued_by')
    op.drop_column('irn_records', 'verification_code')
    op.drop_column('irn_records', 'hash_value')
    
    # Rename meta_data back to metadata
    op.execute("""
    ALTER TABLE irn_records RENAME COLUMN meta_data TO metadata;
    """)
    
    # Drop the enum type
    op.execute("""
    DROP TYPE irn_status;
    """)
