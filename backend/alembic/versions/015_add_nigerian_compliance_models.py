"""add_nigerian_compliance_models

Revision ID: 015_add_nigerian_compliance_models
Revises: 014_add_crm_pos_tables
Create Date: 2025-06-25 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '015_add_nigerian_compliance_models'
down_revision = '014_add_crm_pos_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    accreditation_status_enum = postgresql.ENUM(
        'pending', 'under_review', 'approved', 'rejected', 'expired', 'suspended',
        name='accreditationstatus',
        create_type=False
    )
    compliance_level_enum = postgresql.ENUM(
        'excellent', 'good', 'satisfactory', 'needs_improvement', 'non_compliant',
        name='compliancelevel',
        create_type=False
    )
    
    # Create enum types if they don't exist
    op.execute("DO $$ BEGIN CREATE TYPE accreditationstatus AS ENUM ('pending', 'under_review', 'approved', 'rejected', 'expired', 'suspended'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE compliancelevel AS ENUM ('excellent', 'good', 'satisfactory', 'needs_improvement', 'non_compliant'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # ### Create NITDA Accreditation table ###
    op.create_table('nitda_accreditations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('accreditation_number', sa.String(length=50), nullable=True),
        sa.Column('nigerian_ownership_percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('cac_registration_number', sa.String(length=20), nullable=True),
        sa.Column('cbn_license_status', sa.String(length=20), nullable=True),
        sa.Column('cpn_registration_status', sa.String(length=20), nullable=True),
        sa.Column('status', accreditation_status_enum, nullable=True),
        sa.Column('issued_date', sa.DateTime(), nullable=True),
        sa.Column('expiry_date', sa.DateTime(), nullable=True),
        sa.Column('compliance_requirements', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('accreditation_number')
    )
    op.create_index(op.f('ix_nitda_accreditations_id'), 'nitda_accreditations', ['id'], unique=False)

    # ### Create NDPR Compliance table ###
    op.create_table('ndpr_compliance',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('data_processing_activities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('consent_records', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('privacy_impact_assessments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('breach_incident_log', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('dpo_contact', sa.String(), nullable=True),
        sa.Column('last_audit_date', sa.DateTime(), nullable=True),
        sa.Column('compliance_score', sa.Integer(), nullable=True),
        sa.Column('compliance_level', compliance_level_enum, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ndpr_compliance_id'), 'ndpr_compliance', ['id'], unique=False)

    # ### Create Nigerian Business Registration table ###
    op.create_table('nigerian_business_registrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cac_registration_number', sa.String(length=20), nullable=True),
        sa.Column('business_name', sa.String(length=255), nullable=False),
        sa.Column('registration_date', sa.DateTime(), nullable=True),
        sa.Column('business_type', sa.String(length=50), nullable=True),
        sa.Column('firs_tin', sa.String(length=20), nullable=True),
        sa.Column('state_tax_id', sa.String(length=20), nullable=True),
        sa.Column('local_government_tax_id', sa.String(length=20), nullable=True),
        sa.Column('operating_state', sa.String(length=50), nullable=True),
        sa.Column('local_government_area', sa.String(length=100), nullable=True),
        sa.Column('registered_address', sa.Text(), nullable=True),
        sa.Column('primary_business_activity', sa.String(length=255), nullable=True),
        sa.Column('business_sector', sa.String(length=100), nullable=True),
        sa.Column('annual_revenue_ngn', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('employee_count', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_verified', sa.DateTime(), nullable=True),
        sa.Column('verification_status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_nigerian_business_registrations_id'), 'nigerian_business_registrations', ['id'], unique=False)

    # ### Create FIRS Penalty Tracking table ###
    op.create_table('firs_penalty_tracking',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('violation_type', sa.String(length=100), nullable=False),
        sa.Column('violation_date', sa.DateTime(), nullable=False),
        sa.Column('days_non_compliant', sa.Integer(), nullable=True),
        sa.Column('first_day_penalty', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('subsequent_day_penalty', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('total_penalty', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('payment_status', sa.String(length=20), nullable=True),
        sa.Column('amount_paid', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('payment_plan_id', sa.String(length=50), nullable=True),
        sa.Column('penalty_calculated_date', sa.DateTime(), nullable=True),
        sa.Column('payment_due_date', sa.DateTime(), nullable=True),
        sa.Column('last_payment_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_firs_penalty_tracking_id'), 'firs_penalty_tracking', ['id'], unique=False)

    # ### Create ISO 27001 Compliance table ###
    op.create_table('iso27001_compliance',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('certificate_number', sa.String(length=50), nullable=True),
        sa.Column('certification_body', sa.String(length=100), nullable=True),
        sa.Column('issue_date', sa.DateTime(), nullable=True),
        sa.Column('expiry_date', sa.DateTime(), nullable=True),
        sa.Column('control_status', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('last_audit_date', sa.DateTime(), nullable=True),
        sa.Column('next_audit_date', sa.DateTime(), nullable=True),
        sa.Column('audit_findings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('overall_compliance_score', sa.Integer(), nullable=True),
        sa.Column('compliance_level', compliance_level_enum, nullable=True),
        sa.Column('risk_assessment', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('mitigation_actions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_iso27001_compliance_id'), 'iso27001_compliance', ['id'], unique=False)


def downgrade():
    # ### Drop tables ###
    op.drop_index(op.f('ix_iso27001_compliance_id'), table_name='iso27001_compliance')
    op.drop_table('iso27001_compliance')
    op.drop_index(op.f('ix_firs_penalty_tracking_id'), table_name='firs_penalty_tracking')
    op.drop_table('firs_penalty_tracking')
    op.drop_index(op.f('ix_nigerian_business_registrations_id'), table_name='nigerian_business_registrations')
    op.drop_table('nigerian_business_registrations')
    op.drop_index(op.f('ix_ndpr_compliance_id'), table_name='ndpr_compliance')
    op.drop_table('ndpr_compliance')
    op.drop_index(op.f('ix_nitda_accreditations_id'), table_name='nitda_accreditations')
    op.drop_table('nitda_accreditations')
    
    # ### Drop enum types ###
    op.execute("DROP TYPE IF EXISTS accreditationstatus;")
    op.execute("DROP TYPE IF EXISTS compliancelevel;")