"""Add Nigerian business culture models

Revision ID: 016_add_nigerian_business_models
Revises: 015_add_nigerian_compliance_models
Create Date: 2024-12-29 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '016_add_nigerian_business_models'
down_revision = '015_add_nigerian_compliance_models'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    op.execute("CREATE TYPE languagepreference AS ENUM ('english', 'hausa', 'yoruba', 'igbo')")
    op.execute("CREATE TYPE greetingstyle AS ENUM ('formal', 'traditional', 'modern')")
    op.execute("CREATE TYPE communicationpace AS ENUM ('relationship_first', 'business_first')")
    op.execute("CREATE TYPE approvalstatus AS ENUM ('pending', 'approved', 'rejected', 'escalated')")
    op.execute("CREATE TYPE taxconsolidationtype AS ENUM ('consolidated', 'separate')")

    # Create nigerian_relationship_managers table
    op.create_table('nigerian_relationship_managers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('whatsapp_number', sa.String(20), nullable=True),
        sa.Column('photo_url', sa.String(500), nullable=True),
        sa.Column('office_location', sa.String(255), nullable=True),
        sa.Column('local_language_preference', sa.Enum('english', 'hausa', 'yoruba', 'igbo', name='languagepreference'), default='english'),
        sa.Column('meeting_availability', postgresql.JSONB(), nullable=True),
        sa.Column('timezone', sa.String(50), default='Africa/Lagos'),
        sa.Column('industry_specialization', postgresql.JSONB(), nullable=True),
        sa.Column('client_capacity', sa.Integer, default=50),
        sa.Column('current_client_count', sa.Integer, default=0),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('hired_date', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now())
    )

    # Create nigerian_client_assignments table
    op.create_table('nigerian_client_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('relationship_manager_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('nigerian_relationship_managers.id'), nullable=False),
        sa.Column('assigned_date', sa.DateTime, server_default=sa.func.now()),
        sa.Column('is_primary', sa.Boolean, default=True),
        sa.Column('assignment_reason', sa.Text, nullable=True),
        sa.Column('cultural_preferences', postgresql.JSONB(), nullable=True),
        sa.Column('communication_preferences', postgresql.JSONB(), nullable=True),
        sa.Column('meeting_preferences', postgresql.JSONB(), nullable=True),
        sa.Column('relationship_score', sa.Float, default=0.0),
        sa.Column('last_interaction_date', sa.DateTime, nullable=True),
        sa.Column('interaction_frequency', sa.String(20), default='weekly'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now())
    )

    # Create nigerian_cultural_preferences table
    op.create_table('nigerian_cultural_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False, unique=True),
        sa.Column('greeting_style', sa.Enum('formal', 'traditional', 'modern', name='greetingstyle'), default='formal'),
        sa.Column('communication_pace', sa.Enum('relationship_first', 'business_first', name='communicationpace'), default='relationship_first'),
        sa.Column('relationship_building_time', sa.Integer, default=15),
        sa.Column('hierarchy_acknowledgment', sa.Boolean, default=True),
        sa.Column('gift_exchange_customs', sa.Boolean, default=False),
        sa.Column('whatsapp_business_api', sa.Boolean, default=True),
        sa.Column('voice_calls', sa.Boolean, default=True),
        sa.Column('video_calls', sa.Boolean, default=False),
        sa.Column('in_person_meetings', sa.Boolean, default=True),
        sa.Column('traditional_email', sa.Boolean, default=True),
        sa.Column('primary_language', sa.Enum('english', 'hausa', 'yoruba', 'igbo', name='languagepreference'), default='english'),
        sa.Column('secondary_languages', postgresql.JSONB(), nullable=True),
        sa.Column('respect_titles', sa.Boolean, default=True),
        sa.Column('age_respectful_language', sa.Boolean, default=True),
        sa.Column('gender_appropriate_language', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now())
    )

    # Create nigerian_approval_levels table
    op.create_table('nigerian_approval_levels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('level_name', sa.String(100), nullable=False),
        sa.Column('level_order', sa.Integer, nullable=False),
        sa.Column('amount_limit_ngn', sa.Numeric(15, 2), nullable=False),
        sa.Column('requires_superior_approval', sa.Boolean, default=True),
        sa.Column('requires_board_approval', sa.Boolean, default=False),
        sa.Column('requires_board_ratification', sa.Boolean, default=False),
        sa.Column('conditions', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now())
    )

    # Create nigerian_approval_requests table
    op.create_table('nigerian_approval_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('approval_level_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('nigerian_approval_levels.id'), nullable=False),
        sa.Column('request_type', sa.String(50), nullable=False),
        sa.Column('request_reference', sa.String(100), nullable=False),
        sa.Column('amount_ngn', sa.Numeric(15, 2), nullable=True),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('requester_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('approver_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', 'escalated', name='approvalstatus'), default='pending'),
        sa.Column('submitted_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('approved_at', sa.DateTime, nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),
        sa.Column('escalation_level', sa.Integer, default=0),
        sa.Column('escalated_at', sa.DateTime, nullable=True),
        sa.Column('escalation_reason', sa.Text, nullable=True),
        sa.Column('request_data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now())
    )

    # Create nigerian_conglomerates table
    op.create_table('nigerian_conglomerates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('parent_organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('conglomerate_name', sa.String(255), nullable=False),
        sa.Column('cac_group_registration', sa.String(50), nullable=True),
        sa.Column('tax_consolidation_type', sa.Enum('consolidated', 'separate', name='taxconsolidationtype'), default='separate'),
        sa.Column('primary_business_sector', sa.String(100), nullable=True),
        sa.Column('total_subsidiaries', sa.Integer, default=0),
        sa.Column('total_employees', sa.Integer, nullable=True),
        sa.Column('consolidated_revenue_ngn', sa.Numeric(20, 2), nullable=True),
        sa.Column('board_structure', postgresql.JSONB(), nullable=True),
        sa.Column('governance_model', sa.String(50), default='traditional'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now())
    )

    # Create nigerian_subsidiaries table
    op.create_table('nigerian_subsidiaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conglomerate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('nigerian_conglomerates.id'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('subsidiary_name', sa.String(255), nullable=False),
        sa.Column('cac_registration_number', sa.String(50), nullable=True),
        sa.Column('operating_state', sa.String(50), nullable=True),
        sa.Column('local_government_area', sa.String(100), nullable=True),
        sa.Column('firs_tin', sa.String(20), nullable=True),
        sa.Column('state_tax_id', sa.String(20), nullable=True),
        sa.Column('local_government_tax_id', sa.String(20), nullable=True),
        sa.Column('primary_location', postgresql.JSONB(), nullable=True),
        sa.Column('business_activities', postgresql.JSONB(), nullable=True),
        sa.Column('employee_count', sa.Integer, nullable=True),
        sa.Column('annual_revenue_ngn', sa.Numeric(15, 2), nullable=True),
        sa.Column('ownership_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('shareholding_structure', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('incorporation_date', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now())
    )

    # Create nigerian_business_interactions table
    op.create_table('nigerian_business_interactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('relationship_manager_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('nigerian_relationship_managers.id'), nullable=True),
        sa.Column('interaction_type', sa.String(50), nullable=False),
        sa.Column('interaction_subject', sa.String(255), nullable=True),
        sa.Column('interaction_notes', sa.Text, nullable=True),
        sa.Column('participants', postgresql.JSONB(), nullable=True),
        sa.Column('relationship_building_time', sa.Integer, nullable=True),
        sa.Column('business_discussion_time', sa.Integer, nullable=True),
        sa.Column('cultural_elements_observed', postgresql.JSONB(), nullable=True),
        sa.Column('interaction_outcome', sa.String(50), nullable=True),
        sa.Column('follow_up_required', sa.Boolean, default=False),
        sa.Column('follow_up_date', sa.DateTime, nullable=True),
        sa.Column('interaction_date', sa.DateTime, nullable=False),
        sa.Column('duration_minutes', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now())
    )

    # Create indexes for better performance
    op.create_index('idx_nigerian_client_assignments_org_id', 'nigerian_client_assignments', ['organization_id'])
    op.create_index('idx_nigerian_client_assignments_manager_id', 'nigerian_client_assignments', ['relationship_manager_id'])
    op.create_index('idx_nigerian_approval_requests_org_id', 'nigerian_approval_requests', ['organization_id'])
    op.create_index('idx_nigerian_approval_requests_status', 'nigerian_approval_requests', ['status'])
    op.create_index('idx_nigerian_subsidiaries_conglomerate_id', 'nigerian_subsidiaries', ['conglomerate_id'])
    op.create_index('idx_nigerian_business_interactions_org_id', 'nigerian_business_interactions', ['organization_id'])
    op.create_index('idx_nigerian_business_interactions_date', 'nigerian_business_interactions', ['interaction_date'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_nigerian_business_interactions_date')
    op.drop_index('idx_nigerian_business_interactions_org_id')
    op.drop_index('idx_nigerian_subsidiaries_conglomerate_id')
    op.drop_index('idx_nigerian_approval_requests_status')
    op.drop_index('idx_nigerian_approval_requests_org_id')
    op.drop_index('idx_nigerian_client_assignments_manager_id')
    op.drop_index('idx_nigerian_client_assignments_org_id')

    # Drop tables
    op.drop_table('nigerian_business_interactions')
    op.drop_table('nigerian_subsidiaries')
    op.drop_table('nigerian_conglomerates')
    op.drop_table('nigerian_approval_requests')
    op.drop_table('nigerian_approval_levels')
    op.drop_table('nigerian_cultural_preferences')
    op.drop_table('nigerian_client_assignments')
    op.drop_table('nigerian_relationship_managers')

    # Drop enum types
    op.execute("DROP TYPE taxconsolidationtype")
    op.execute("DROP TYPE approvalstatus")
    op.execute("DROP TYPE communicationpace")
    op.execute("DROP TYPE greetingstyle")
    op.execute("DROP TYPE languagepreference")