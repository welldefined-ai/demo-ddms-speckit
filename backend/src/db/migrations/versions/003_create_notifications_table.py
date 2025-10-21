"""Create notifications table

Revision ID: 003
Revises: 002
Create Date: 2025-10-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('type', sa.Enum('DEVICE_DISCONNECT', 'DEVICE_ALERT', 'SYSTEM', name='notificationtype'), nullable=False),
        sa.Column('severity', sa.Enum('INFO', 'WARNING', 'ERROR', 'CRITICAL', name='notificationseverity'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', JSON, nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
    )

    # Create indexes for efficient queries
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_device_id', 'notifications', ['device_id'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])

    # Composite index for unread notifications query (user_id, read_at null, created_at desc)
    op.create_index(
        'ix_notifications_user_unread',
        'notifications',
        ['user_id', 'read_at', 'created_at'],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_notifications_user_unread', 'notifications')
    op.drop_index('ix_notifications_created_at', 'notifications')
    op.drop_index('ix_notifications_device_id', 'notifications')
    op.drop_index('ix_notifications_user_id', 'notifications')

    # Drop table
    op.drop_table('notifications')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS notificationseverity')
    op.execute('DROP TYPE IF EXISTS notificationtype')
