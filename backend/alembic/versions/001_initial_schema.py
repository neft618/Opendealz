"""initial_schema

Revision ID: 001
Revises: 
Create Date: 2026-05-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String, nullable=False, unique=True),
        sa.Column('password_hash', sa.String, nullable=False),
        sa.Column('full_name', sa.String, nullable=False),
        sa.Column('role', sa.Enum('customer', 'executor', 'admin', name='user_role', create_type=False), nullable=False, server_default='customer'),
        sa.Column('is_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('wallet_address', sa.String(42), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_users_email', 'users', ['email'])

    # profiles table
    op.create_table(
        'profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('bio', sa.Text, nullable=True),
        sa.Column('skills', sa.Text, nullable=True),
        sa.Column('specialization', sa.Enum('web_development', 'mobile_development', 'data_science', 'design', 'marketing', 'other', name='specialization', create_type=False), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('user_id', name='uq_profiles_user_id'),
    )
    op.create_index('idx_profiles_user_id', 'profiles', ['user_id'])

    # portfolios table
    op.create_table(
        'portfolios',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('file_url', sa.String, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_portfolios_profile_id', 'portfolios', ['profile_id'])

    # orders table
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.String, nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('status', sa.Enum('open', 'in_progress', 'closed', 'cancelled', name='order_status', create_type=False), nullable=False, server_default='open'),
        sa.Column('budget', sa.Numeric(12, 2), nullable=False),
        sa.Column('deadline', sa.Date, nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('executor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('budget > 0', name='chk_orders_budget_positive'),
    )
    op.create_index('idx_orders_customer_id', 'orders', ['customer_id'])
    op.create_index('idx_orders_status', 'orders', ['status'])

    # applications table
    op.create_table(
        'applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('executor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cover_letter', sa.Text, nullable=False),
        sa.Column('proposed_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('status', sa.Enum('pending', 'accepted', 'rejected', name='application_status', create_type=False), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('order_id', 'executor_id', name='uq_application_order_executor'),
        sa.CheckConstraint('proposed_price > 0', name='chk_applications_price_positive'),
    )
    op.create_index('idx_applications_order_id', 'applications', ['order_id'])
    op.create_index('idx_applications_executor_id', 'applications', ['executor_id'])

    # contracts table
    op.create_table(
        'contracts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orders.id', ondelete='RESTRICT'), nullable=False, unique=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('executor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', sa.Enum('draft', 'signed', 'in_progress', 'completed', 'disputed', 'cancelled', name='contract_status', create_type=False), nullable=False, server_default='draft'),
        sa.Column('total_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('platform_fee', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('payment_type', sa.Enum('fixed', 'hourly', 'milestone', name='payment_type', create_type=False), nullable=False),
        sa.Column('review_period_days', sa.Integer, nullable=False, server_default='3'),
        sa.Column('contract_hash', sa.String(64), nullable=True),
        sa.Column('signed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('customer_signed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('executor_signed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('order_id', name='uq_contracts_order_id'),
    )
    op.create_index('idx_contracts_customer_id', 'contracts', ['customer_id'])
    op.create_index('idx_contracts_executor_id', 'contracts', ['executor_id'])
    op.create_index('idx_contracts_status', 'contracts', ['status'])

    # contract_clauses table
    op.create_table(
        'contract_clauses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('contracts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('clause_type', sa.Enum('subject_description', 'timeline', 'payment_terms', 'termination_conditions', 'result_review_period', 'refund_policy', 'platform_commission', 'ip_rights', 'confidentiality', name='clause_type', create_type=False), nullable=False),
        sa.Column('content', sa.Text, nullable=False, server_default=''),
        sa.Column('position', sa.Integer, nullable=False),
        sa.Column('is_mandatory', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_contract_clauses_contract_id', 'contract_clauses', ['contract_id'])

    # milestones table
    op.create_table(
        'milestones',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('contracts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('deadline', sa.Date, nullable=False),
        sa.Column('status', sa.Enum('pending', 'in_progress', 'approved', 'rejected', name='milestone_status', create_type=False), nullable=False, server_default='pending'),
        sa.Column('position', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('amount > 0', name='chk_milestones_amount_positive'),
    )
    op.create_index('idx_milestones_contract_id', 'milestones', ['contract_id'])

    # deliverables table
    op.create_table(
        'deliverables',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('contracts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('milestone_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('milestones.id', ondelete='SET NULL'), nullable=True),
        sa.Column('file_url', sa.String, nullable=False),
        sa.Column('file_name', sa.String, nullable=False),
        sa.Column('file_size', sa.Integer, nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('submitted_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_deliverables_contract_id', 'deliverables', ['contract_id'])

    # escrow_transactions table
    op.create_table(
        'escrow_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('contracts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.Enum('lock', 'release', 'refund', 'fee', name='escrow_tx_type', create_type=False), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('status', sa.Enum('pending', 'confirmed', 'failed', name='escrow_tx_status', create_type=False), nullable=False, server_default='pending'),
        sa.Column('initiated_by', sa.Enum('customer', 'executor', 'shared', 'system', name='initiated_by', create_type=False), nullable=False),
        sa.Column('tx_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_escrow_contract_id', 'escrow_transactions', ['contract_id'])
    op.create_index('idx_escrow_tx_hash', 'escrow_transactions', ['tx_hash'])

    # disputes table
    op.create_table(
        'disputes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('contracts.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('initiated_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.Enum('open', 'under_review', 'resolved', name='dispute_status', create_type=False), nullable=False, server_default='open'),
        sa.Column('resolution', sa.Enum('executor', 'customer', 'shared', name='dispute_resolution', create_type=False), nullable=True),
        sa.Column('resolution_comment', sa.Text, nullable=True),
        sa.Column('resolved_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_disputes_contract_id', 'disputes', ['contract_id'])
    op.create_index('idx_disputes_status', 'disputes', ['status'])

    # dispute_messages table
    op.create_table(
        'dispute_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('dispute_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('disputes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('file_url', sa.String, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_dispute_messages_dispute_id', 'dispute_messages', ['dispute_id'])

    # reviews table
    op.create_table(
        'reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('contracts.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('recipient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('rating', sa.SmallInteger, nullable=False),
        sa.Column('comment', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('contract_id', 'author_id', name='uq_review_contract_author'),
        sa.CheckConstraint('rating BETWEEN 1 AND 5', name='chk_reviews_rating'),
    )
    op.create_index('idx_reviews_recipient_id', 'reviews', ['recipient_id'])
    op.create_index('idx_reviews_contract_id', 'reviews', ['contract_id'])

    # notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.Enum('contract', 'payment', 'dispute', 'system', name='notification_type', create_type=False), nullable=False),
        sa.Column('title', sa.String, nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('is_read', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('related_entity_type', sa.String, nullable=True),
        sa.Column('related_entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_notifications_user_id', 'notifications', ['user_id'])
    op.execute(
        "CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = false"
    )

    # audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_type', sa.String, nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('payload', postgresql.JSONB, nullable=True),
        sa.Column('tx_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('ip_address', sa.String, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_audit_log_entity', 'audit_log', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_log_tx_hash', 'audit_log', ['tx_hash'])

    # set_updated_at trigger function + apply to tables
    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    for table in ['users', 'profiles', 'portfolios', 'orders', 'applications', 'contracts',
                  'contract_clauses', 'milestones', 'deliverables', 'escrow_transactions',
                  'disputes', 'notifications']:
        op.execute(f"""
            CREATE TRIGGER set_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """)


def downgrade() -> None:
    for table in ['users', 'profiles', 'portfolios', 'orders', 'applications', 'contracts',
                  'contract_clauses', 'milestones', 'deliverables', 'escrow_transactions',
                  'disputes', 'notifications']:
        op.execute(f"DROP TRIGGER IF EXISTS set_{table}_updated_at ON {table}")

    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")

    for t in ['audit_log', 'notifications', 'reviews', 'dispute_messages', 'disputes',
              'escrow_transactions', 'deliverables', 'milestones', 'contract_clauses',
              'contracts', 'applications', 'orders', 'portfolios', 'profiles', 'users']:
        op.drop_table(t)

    for e in ['user_role', 'specialization', 'order_status', 'application_status',
              'contract_status', 'payment_type', 'clause_type', 'milestone_status',
              'escrow_tx_type', 'escrow_tx_status', 'initiated_by', 'dispute_status',
              'dispute_resolution', 'notification_type']:
        op.execute(f"DROP TYPE IF EXISTS {e}")
