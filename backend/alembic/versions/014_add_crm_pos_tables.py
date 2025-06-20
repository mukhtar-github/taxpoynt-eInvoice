"""Add CRM and POS integration tables

Revision ID: 014_add_crm_pos_tables
Revises: 013_add_app_functionality_tables
Create Date: 2025-06-18 09:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '014_add_crm_pos_tables'
down_revision = '013_add_app_functionality_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Implement the CRM and POS integration tables following the multi-step approach:
    1. Check for dependency tables
    2. Create tables without foreign key constraints
    3. Add foreign key constraints separately if dependencies exist
    4. Set up table partitioning for high-volume tables
    """
    # Step 1: Check if dependency tables exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()
    
    # Make sure required tables exist
    required_tables = ['organizations', 'users', 'invoices']
    missing_tables = [table for table in required_tables if table not in tables]
    
    # Step 2: Create enums first
    op.execute("CREATE TYPE crm_type AS ENUM ('hubspot', 'salesforce', 'pipedrive', 'zoho', 'custom');")
    op.execute("CREATE TYPE pos_type AS ENUM ('square', 'toast', 'lightspeed', 'flutterwave', 'paystack', 'custom');")
    
    # Step 3: Create the tables without foreign key constraints initially

    # CRM Connections table
    op.create_table(
        'crm_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('crm_type', sa.Enum('hubspot', 'salesforce', 'pipedrive', 'zoho', 'custom', name='crm_type'), nullable=False),
        sa.Column('connection_name', sa.String(255)),
        sa.Column('credentials_encrypted', sa.Text),
        sa.Column('connection_settings', postgresql.JSONB, nullable=True),
        sa.Column('webhook_url', sa.String(500), nullable=True),
        sa.Column('webhook_secret', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, server_default=sa.text('true')),
        sa.Column('last_sync_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now())
    )
    
    # Create indexes for CRM connections
    op.create_index('idx_crm_connections_user_id', 'crm_connections', ['user_id'])
    op.create_index('idx_crm_connections_organization_id', 'crm_connections', ['organization_id'])
    op.create_index('idx_crm_connections_crm_type', 'crm_connections', ['crm_type'])
    
    # CRM Deals table
    op.create_table(
        'crm_deals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('external_deal_id', sa.String(255), nullable=False),
        sa.Column('deal_title', sa.String(255)),
        sa.Column('deal_amount', sa.Numeric(15, 2)),
        sa.Column('customer_data', postgresql.JSONB),
        sa.Column('deal_stage', sa.String(100)),
        sa.Column('expected_close_date', sa.DateTime, nullable=True),
        sa.Column('invoice_generated', sa.Boolean, server_default=sa.text('false')),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deal_metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now())
    )
    
    # Create indexes for CRM deals
    op.create_index('idx_crm_deals_connection_id', 'crm_deals', ['connection_id'])
    op.create_index('idx_crm_deals_external_deal_id', 'crm_deals', ['external_deal_id'])
    op.create_index('idx_crm_deals_invoice_id', 'crm_deals', ['invoice_id'])
    op.create_index('idx_crm_deals_connection_stage', 'crm_deals', ['connection_id', 'deal_stage'])
    
    # POS Connections table
    op.create_table(
        'pos_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pos_type', sa.Enum('square', 'toast', 'lightspeed', 'flutterwave', 'paystack', 'custom', name='pos_type'), nullable=False),
        sa.Column('location_name', sa.String(255)),
        sa.Column('credentials_encrypted', sa.Text),
        sa.Column('connection_settings', postgresql.JSONB, nullable=True),
        sa.Column('webhook_url', sa.String(500), nullable=True),
        sa.Column('webhook_secret', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, server_default=sa.text('true')),
        sa.Column('last_sync_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now())
    )
    
    # Create indexes for POS connections
    op.create_index('idx_pos_connections_user_id', 'pos_connections', ['user_id'])
    op.create_index('idx_pos_connections_organization_id', 'pos_connections', ['organization_id'])
    op.create_index('idx_pos_connections_pos_type', 'pos_connections', ['pos_type'])
    
    # Step 4: Create the POS transactions table with partitioning
    # First create the parent table with partitioning configuration
    op.execute("""
    CREATE TABLE pos_transactions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        connection_id UUID NOT NULL,
        external_transaction_id VARCHAR(255) NOT NULL,
        transaction_amount DECIMAL(15,2),
        tax_amount DECIMAL(15,2),
        items JSONB,
        customer_data JSONB,
        transaction_timestamp TIMESTAMP NOT NULL,
        invoice_generated BOOLEAN DEFAULT FALSE,
        invoice_transmitted BOOLEAN DEFAULT FALSE,
        invoice_id UUID,
        processing_errors JSONB,
        transaction_metadata JSONB,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP
    ) PARTITION BY RANGE (transaction_timestamp);
    """)
    
    # Create indexes for POS transactions (on parent table)
    op.create_index('idx_pos_transactions_connection_id', 'pos_transactions', ['connection_id'])
    op.create_index('idx_pos_transactions_external_id', 'pos_transactions', ['external_transaction_id'])
    op.create_index('idx_pos_transactions_invoice_id', 'pos_transactions', ['invoice_id'])
    op.create_index('idx_pos_transactions_timestamp', 'pos_transactions', ['transaction_timestamp'])
    op.create_index('idx_pos_transactions_conn_timestamp', 'pos_transactions', ['connection_id', 'transaction_timestamp'])
    op.create_index('idx_pos_transaction_invoice_status', 'pos_transactions', ['connection_id', 'invoice_generated', 'invoice_transmitted'])
    
    # Step 5: Create initial partitions for high-volume transaction data (current and next 6 months)
    # Starting from current month (June 2025)
    # This follows a pattern where each partition covers a month's transactions
    
    partitions = [
        ('pos_transactions_y2025m06', '2025-06-01', '2025-07-01'),
        ('pos_transactions_y2025m07', '2025-07-01', '2025-08-01'),
        ('pos_transactions_y2025m08', '2025-08-01', '2025-09-01'),
        ('pos_transactions_y2025m09', '2025-09-01', '2025-10-01'),
        ('pos_transactions_y2025m10', '2025-10-01', '2025-11-01'),
        ('pos_transactions_y2025m11', '2025-11-01', '2025-12-01'),
        ('pos_transactions_y2025m12', '2025-12-01', '2026-01-01'),
    ]
    
    for partition_name, start_date, end_date in partitions:
        op.execute(f"""
        CREATE TABLE {partition_name} PARTITION OF pos_transactions
            FOR VALUES FROM ('{start_date}') TO ('{end_date}');
        """)
    
    # Step 6: Add foreign key constraints only if dependency tables exist
    if not missing_tables:
        # All required tables exist, so we can add the foreign key constraints
        op.create_foreign_key('fk_crm_connections_user', 'crm_connections', 'users', ['user_id'], ['id'])
        op.create_foreign_key('fk_crm_connections_org', 'crm_connections', 'organizations', ['organization_id'], ['id'])
        
        op.create_foreign_key('fk_crm_deals_connection', 'crm_deals', 'crm_connections', ['connection_id'], ['id'])
        op.create_foreign_key('fk_crm_deals_invoice', 'crm_deals', 'invoices', ['invoice_id'], ['id'])
        
        op.create_foreign_key('fk_pos_connections_user', 'pos_connections', 'users', ['user_id'], ['id'])
        op.create_foreign_key('fk_pos_connections_org', 'pos_connections', 'organizations', ['organization_id'], ['id'])
        
        op.create_foreign_key('fk_pos_transactions_connection', 'pos_transactions', 'pos_connections', ['connection_id'], ['id'])
        op.create_foreign_key('fk_pos_transactions_invoice', 'pos_transactions', 'invoices', ['invoice_id'], ['id'])
    else:
        # Log that some foreign keys couldn't be added due to missing dependencies
        print(f"Warning: The following tables are missing, so some foreign key constraints were not added: {missing_tables}")
        print("You must manually add these constraints after the missing tables are created.")


def downgrade() -> None:
    """
    Revert the CRM and POS integration tables.
    Drop tables and enums in reverse order of creation to avoid dependency issues.
    """
    # Drop tables
    for partition_name in [
        'pos_transactions_y2025m06', 
        'pos_transactions_y2025m07', 
        'pos_transactions_y2025m08',
        'pos_transactions_y2025m09',
        'pos_transactions_y2025m10',
        'pos_transactions_y2025m11',
        'pos_transactions_y2025m12',
    ]:
        try:
            op.execute(f"DROP TABLE IF EXISTS {partition_name};")
        except Exception:
            # If partition was already dropped with parent table, ignore error
            pass
            
    op.drop_table('pos_transactions')
    op.drop_table('crm_deals')
    op.drop_table('pos_connections')
    op.drop_table('crm_connections')
    
    # Drop custom enums
    op.execute("DROP TYPE IF EXISTS pos_type;")
    op.execute("DROP TYPE IF EXISTS crm_type;")
