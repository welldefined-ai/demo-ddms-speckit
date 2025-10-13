"""Add TimescaleDB continuous aggregates for readings

Revision ID: 002
Revises: 001
Create Date: 2025-10-13

Creates continuous aggregate views for efficient time-series data querying:
- readings_1min: 1-minute buckets with AVG, MIN, MAX, COUNT
- readings_1hour: 1-hour buckets with AVG, MIN, MAX, COUNT
- readings_1day: 1-day buckets with AVG, MIN, MAX, COUNT

These materialized views are automatically maintained by TimescaleDB and
significantly improve query performance for historical data analysis.

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create continuous aggregate views for different time intervals.

    Note: These views only work with TimescaleDB/PostgreSQL.
    For SQLite testing, these statements will be skipped.
    """

    # Check if we're running on PostgreSQL (TimescaleDB)
    # SQLite migrations will skip TimescaleDB-specific features
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':

        # Create 1-minute continuous aggregate
        # Useful for recent data (last few hours)
        op.execute("""
            CREATE MATERIALIZED VIEW readings_1min
            WITH (timescaledb.continuous) AS
            SELECT
                device_id,
                time_bucket('1 minute', timestamp) AS bucket,
                AVG(value) AS avg_value,
                MIN(value) AS min_value,
                MAX(value) AS max_value,
                COUNT(*) AS count
            FROM readings
            GROUP BY device_id, bucket
            WITH NO DATA;
        """)

        # Add refresh policy: auto-refresh every 1 minute for last 1 hour of data
        op.execute("""
            SELECT add_continuous_aggregate_policy('readings_1min',
                start_offset => INTERVAL '1 hour',
                end_offset => INTERVAL '1 minute',
                schedule_interval => INTERVAL '1 minute');
        """)

        # Create indexes on continuous aggregate for better query performance
        op.execute("""
            CREATE INDEX idx_readings_1min_device_bucket
            ON readings_1min (device_id, bucket DESC);
        """)


        # Create 1-hour continuous aggregate
        # Useful for data from last few days to weeks
        op.execute("""
            CREATE MATERIALIZED VIEW readings_1hour
            WITH (timescaledb.continuous) AS
            SELECT
                device_id,
                time_bucket('1 hour', timestamp) AS bucket,
                AVG(value) AS avg_value,
                MIN(value) AS min_value,
                MAX(value) AS max_value,
                COUNT(*) AS count
            FROM readings
            GROUP BY device_id, bucket
            WITH NO DATA;
        """)

        # Add refresh policy: auto-refresh every 10 minutes for last 7 days of data
        op.execute("""
            SELECT add_continuous_aggregate_policy('readings_1hour',
                start_offset => INTERVAL '7 days',
                end_offset => INTERVAL '1 hour',
                schedule_interval => INTERVAL '10 minutes');
        """)

        # Create indexes
        op.execute("""
            CREATE INDEX idx_readings_1hour_device_bucket
            ON readings_1hour (device_id, bucket DESC);
        """)


        # Create 1-day continuous aggregate
        # Useful for long-term historical analysis (weeks to months)
        op.execute("""
            CREATE MATERIALIZED VIEW readings_1day
            WITH (timescaledb.continuous) AS
            SELECT
                device_id,
                time_bucket('1 day', timestamp) AS bucket,
                AVG(value) AS avg_value,
                MIN(value) AS min_value,
                MAX(value) AS max_value,
                COUNT(*) AS count
            FROM readings
            GROUP BY device_id, bucket
            WITH NO DATA;
        """)

        # Add refresh policy: auto-refresh every 1 hour for last 90 days of data
        op.execute("""
            SELECT add_continuous_aggregate_policy('readings_1day',
                start_offset => INTERVAL '90 days',
                end_offset => INTERVAL '1 day',
                schedule_interval => INTERVAL '1 hour');
        """)

        # Create indexes
        op.execute("""
            CREATE INDEX idx_readings_1day_device_bucket
            ON readings_1day (device_id, bucket DESC);
        """)

        # Note: Initial data refresh will happen automatically via the policies
        # Or can be manually triggered with:
        # CALL refresh_continuous_aggregate('readings_1min', NULL, NULL);
        # CALL refresh_continuous_aggregate('readings_1hour', NULL, NULL);
        # CALL refresh_continuous_aggregate('readings_1day', NULL, NULL);


def downgrade() -> None:
    """
    Drop continuous aggregate views and their policies.
    """

    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        # Drop continuous aggregates (policies are automatically removed)
        op.execute("DROP MATERIALIZED VIEW IF EXISTS readings_1day CASCADE;")
        op.execute("DROP MATERIALIZED VIEW IF EXISTS readings_1hour CASCADE;")
        op.execute("DROP MATERIALIZED VIEW IF EXISTS readings_1min CASCADE;")
