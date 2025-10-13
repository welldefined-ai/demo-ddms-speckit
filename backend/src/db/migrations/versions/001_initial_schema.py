"""Initial schema with TimescaleDB hypertable

Revision ID: 001
Revises:
Create Date: 2025-10-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('OWNER', 'ADMIN', 'READ_ONLY', name='userrole'), nullable=False),
        sa.Column('language_preference', sa.String(2), default='en', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_users_username', 'users', ['username'])

    # Create devices table
    op.create_table(
        'devices',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('modbus_ip', sa.String(45), nullable=False),
        sa.Column('modbus_port', sa.Integer, default=502, nullable=False),
        sa.Column('modbus_slave_id', sa.Integer, nullable=False),
        sa.Column('modbus_register', sa.Integer, nullable=False),
        sa.Column('modbus_register_count', sa.Integer, default=1, nullable=False),
        sa.Column('unit', sa.String(20), nullable=False),
        sa.Column('sampling_interval', sa.Integer, nullable=False),
        sa.Column('threshold_warning_lower', sa.Float, nullable=True),
        sa.Column('threshold_warning_upper', sa.Float, nullable=True),
        sa.Column('threshold_critical_lower', sa.Float, nullable=True),
        sa.Column('threshold_critical_upper', sa.Float, nullable=True),
        sa.Column('retention_days', sa.Integer, default=90, nullable=False),
        sa.Column('status', sa.Enum('ONLINE', 'OFFLINE', 'ERROR', name='devicestatus'), default='OFFLINE', nullable=False),
        sa.Column('last_reading_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_devices_name', 'devices', ['name'])

    # Create groups table
    op.create_table(
        'groups',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_groups_name', 'groups', ['name'])

    # Create configuration table
    op.create_table(
        'configuration',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('system_name', sa.String(100), default='DDMS - Device Data Monitoring System', nullable=False),
        sa.Column('data_retention_days_default', sa.Integer, default=90, nullable=False),
        sa.Column('backup_enabled', sa.Boolean, default=True, nullable=False),
        sa.Column('backup_schedule', sa.String(100), default='0 2 * * *', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('data_retention_days_default > 0', name='chk_positive_retention'),
    )

    # Create device_groups association table
    op.create_table(
        'device_groups',
        sa.Column('device_id', UUID(as_uuid=True), nullable=False),
        sa.Column('group_id', UUID(as_uuid=True), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('device_id', 'group_id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('device_id', 'group_id', name='uq_device_group'),
    )

    # Create readings table (will be converted to TimescaleDB hypertable)
    op.create_table(
        'readings',
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('device_id', UUID(as_uuid=True), nullable=False),
        sa.Column('value', sa.Float, nullable=False),
        sa.PrimaryKeyConstraint('timestamp', 'device_id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_readings_device_id', 'readings', ['device_id'])
    op.create_index('idx_readings_device_timestamp', 'readings', ['device_id', 'timestamp'])

    # Convert readings table to TimescaleDB hypertable
    # Partition by timestamp with 7-day chunks
    op.execute("""
        SELECT create_hypertable(
            'readings',
            'timestamp',
            chunk_time_interval => INTERVAL '7 days',
            if_not_exists => TRUE
        );
    """)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('readings')
    op.drop_table('device_groups')
    op.drop_table('configuration')
    op.drop_table('groups')
    op.drop_table('devices')
    op.drop_table('users')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS devicestatus')
    op.execute('DROP TYPE IF EXISTS userrole')
