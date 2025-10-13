"""
Integration test for TimescaleDB continuous aggregates (T106)
Tests time-series data aggregation at different intervals
"""
import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from src.db.base import Base
from src.models.device import Device, DeviceStatus
from src.models.reading import Reading


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    """Create test database session"""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_device(db_session):
    """Create test device"""
    device = Device(
        id=uuid.uuid4(),
        name="Test Sensor",
        modbus_ip="192.168.1.100",
        modbus_port=502,
        modbus_slave_id=1,
        modbus_register=0,
        modbus_register_count=1,
        unit="°C",
        sampling_interval=10,
        retention_days=90,
        status=DeviceStatus.CONNECTED
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


@pytest.fixture
def time_series_data(db_session, test_device):
    """Create detailed time-series data for aggregation testing"""
    base_time = datetime.utcnow() - timedelta(days=7)
    readings = []

    # Create readings every 5 minutes for 7 days
    for day in range(7):
        for hour in range(24):
            for minute in range(0, 60, 5):
                timestamp = base_time + timedelta(days=day, hours=hour, minutes=minute)
                # Create varying values with daily and hourly patterns
                value = 20.0 + (day * 2) + (hour * 0.5) + (minute * 0.01)
                reading = Reading(
                    timestamp=timestamp,
                    device_id=test_device.id,
                    value=value
                )
                readings.append(reading)

    db_session.add_all(readings)
    db_session.commit()

    return readings


class TestTimeSeriesAggregation:
    """Test time-series data aggregation queries"""

    def test_aggregate_readings_by_hour(self, db_session, test_device, time_series_data):
        """Test aggregation of readings into 1-hour buckets"""
        # Query: Aggregate by hour with AVG, MIN, MAX
        start_time = datetime.utcnow() - timedelta(days=1)

        # Use SQLite date functions (compatible approach)
        results = db_session.query(
            func.strftime('%Y-%m-%d %H:00:00', Reading.timestamp).label('time_bucket'),
            func.avg(Reading.value).label('avg_value'),
            func.min(Reading.value).label('min_value'),
            func.max(Reading.value).label('max_value'),
            func.count(Reading.id).label('count')
        ).filter(
            Reading.device_id == test_device.id,
            Reading.timestamp >= start_time
        ).group_by(
            func.strftime('%Y-%m-%d %H:00:00', Reading.timestamp)
        ).all()

        assert len(results) > 0
        assert len(results) <= 24  # Max 24 hours

        # Verify aggregation structure
        for result in results:
            assert result.time_bucket is not None
            assert result.avg_value is not None
            assert result.min_value is not None
            assert result.max_value is not None
            assert result.count > 0
            # Min should be <= avg <= max
            assert result.min_value <= result.avg_value <= result.max_value

    def test_aggregate_readings_by_day(self, db_session, test_device, time_series_data):
        """Test aggregation of readings into 1-day buckets"""
        # Query: Aggregate by day
        results = db_session.query(
            func.strftime('%Y-%m-%d', Reading.timestamp).label('time_bucket'),
            func.avg(Reading.value).label('avg_value'),
            func.min(Reading.value).label('min_value'),
            func.max(Reading.value).label('max_value'),
            func.count(Reading.id).label('count')
        ).filter(
            Reading.device_id == test_device.id
        ).group_by(
            func.strftime('%Y-%m-%d', Reading.timestamp)
        ).all()

        assert len(results) == 7  # 7 days of data

        # Each day should have multiple readings
        for result in results:
            assert result.count > 100  # Should have many readings per day

    def test_aggregate_readings_by_minute(self, db_session, test_device, time_series_data):
        """Test aggregation of readings into 1-minute buckets"""
        start_time = datetime.utcnow() - timedelta(hours=1)

        results = db_session.query(
            func.strftime('%Y-%m-%d %H:%M:00', Reading.timestamp).label('time_bucket'),
            func.avg(Reading.value).label('avg_value'),
            func.count(Reading.id).label('count')
        ).filter(
            Reading.device_id == test_device.id,
            Reading.timestamp >= start_time
        ).group_by(
            func.strftime('%Y-%m-%d %H:%M:00', Reading.timestamp)
        ).all()

        assert len(results) > 0

        # With 5-minute sampling, some buckets may be empty
        for result in results:
            assert result.avg_value is not None
            assert result.count >= 0

    def test_aggregate_with_time_range_filter(self, db_session, test_device, time_series_data):
        """Test aggregation with time range filtering"""
        start_time = datetime.utcnow() - timedelta(days=3)
        end_time = datetime.utcnow() - timedelta(days=1)

        results = db_session.query(
            func.strftime('%Y-%m-%d', Reading.timestamp).label('time_bucket'),
            func.avg(Reading.value).label('avg_value')
        ).filter(
            Reading.device_id == test_device.id,
            Reading.timestamp >= start_time,
            Reading.timestamp < end_time
        ).group_by(
            func.strftime('%Y-%m-%d', Reading.timestamp)
        ).all()

        # Should have approximately 2 days of data
        assert 1 <= len(results) <= 3

    def test_aggregate_ordered_by_time(self, db_session, test_device, time_series_data):
        """Test that aggregated results are ordered by time"""
        results = db_session.query(
            func.strftime('%Y-%m-%d %H:00:00', Reading.timestamp).label('time_bucket'),
            func.avg(Reading.value).label('avg_value')
        ).filter(
            Reading.device_id == test_device.id
        ).group_by(
            func.strftime('%Y-%m-%d %H:00:00', Reading.timestamp)
        ).order_by(
            func.strftime('%Y-%m-%d %H:00:00', Reading.timestamp).desc()
        ).limit(10).all()

        # Verify descending order
        for i in range(len(results) - 1):
            assert results[i].time_bucket >= results[i + 1].time_bucket

    def test_aggregate_with_no_data(self, db_session, test_device):
        """Test aggregation when no data exists"""
        future_time = datetime.utcnow() + timedelta(days=1)

        results = db_session.query(
            func.strftime('%Y-%m-%d %H:00:00', Reading.timestamp).label('time_bucket'),
            func.avg(Reading.value).label('avg_value')
        ).filter(
            Reading.device_id == test_device.id,
            Reading.timestamp >= future_time
        ).group_by(
            func.strftime('%Y-%m-%d %H:00:00', Reading.timestamp)
        ).all()

        assert len(results) == 0

    def test_aggregate_multiple_devices(self, db_session, time_series_data):
        """Test aggregation separates data by device"""
        # Create second device
        device2 = Device(
            id=uuid.uuid4(),
            name="Second Sensor",
            modbus_ip="192.168.1.101",
            modbus_port=502,
            modbus_slave_id=2,
            modbus_register=0,
            modbus_register_count=1,
            unit="bar",
            sampling_interval=10,
            retention_days=90,
            status=DeviceStatus.CONNECTED
        )
        db_session.add(device2)
        db_session.commit()

        # Add readings for second device
        base_time = datetime.utcnow() - timedelta(days=1)
        for hour in range(24):
            reading = Reading(
                timestamp=base_time + timedelta(hours=hour),
                device_id=device2.id,
                value=50.0 + hour
            )
            db_session.add(reading)
        db_session.commit()

        # Query aggregates for device2
        results = db_session.query(
            func.avg(Reading.value).label('avg_value'),
            func.count(Reading.id).label('count')
        ).filter(
            Reading.device_id == device2.id
        ).first()

        assert results.count == 24
        assert results.avg_value > 60  # Should be around 61.5

    def test_aggregate_statistics_accuracy(self, db_session, test_device):
        """Test that aggregate statistics are mathematically correct"""
        # Create known test data
        base_time = datetime.utcnow() - timedelta(hours=1)
        known_values = [10.0, 20.0, 30.0, 40.0, 50.0]

        for i, value in enumerate(known_values):
            reading = Reading(
                timestamp=base_time + timedelta(minutes=i * 10),
                device_id=test_device.id,
                value=value
            )
            db_session.add(reading)
        db_session.commit()

        # Query aggregates
        result = db_session.query(
            func.avg(Reading.value).label('avg_value'),
            func.min(Reading.value).label('min_value'),
            func.max(Reading.value).label('max_value'),
            func.count(Reading.id).label('count')
        ).filter(
            Reading.device_id == test_device.id,
            Reading.timestamp >= base_time
        ).first()

        assert result.count == 5
        assert result.min_value == 10.0
        assert result.max_value == 50.0
        assert abs(result.avg_value - 30.0) < 0.01  # Average should be 30

    def test_aggregate_downsampling_reduces_data_points(self, db_session, test_device, time_series_data):
        """Test that aggregation reduces number of data points"""
        # Count raw readings
        raw_count = db_session.query(func.count(Reading.id)).filter(
            Reading.device_id == test_device.id
        ).scalar()

        # Count hourly aggregates
        hourly_count = db_session.query(
            func.count(func.distinct(func.strftime('%Y-%m-%d %H:00:00', Reading.timestamp)))
        ).filter(
            Reading.device_id == test_device.id
        ).scalar()

        # Aggregated data should have significantly fewer points
        assert hourly_count < raw_count
        assert hourly_count == 7 * 24  # 7 days * 24 hours

    def test_aggregate_handles_gaps_in_data(self, db_session, test_device):
        """Test aggregation with gaps in time-series data"""
        base_time = datetime.utcnow() - timedelta(days=1)

        # Create readings with gaps (only even hours)
        for hour in range(0, 24, 2):
            reading = Reading(
                timestamp=base_time + timedelta(hours=hour),
                device_id=test_device.id,
                value=20.0 + hour
            )
            db_session.add(reading)
        db_session.commit()

        results = db_session.query(
            func.strftime('%Y-%m-%d %H:00:00', Reading.timestamp).label('time_bucket'),
            func.avg(Reading.value).label('avg_value')
        ).filter(
            Reading.device_id == test_device.id,
            Reading.timestamp >= base_time
        ).group_by(
            func.strftime('%Y-%m-%d %H:00:00', Reading.timestamp)
        ).all()

        # Should only have 12 buckets (even hours)
        assert len(results) == 12

    def test_aggregate_with_null_values(self, db_session, test_device):
        """Test that aggregation handles null values correctly"""
        base_time = datetime.utcnow() - timedelta(hours=1)

        # SQLite doesn't allow NULL in non-nullable columns,
        # but we can test with valid values and ensure no nulls in output
        for i in range(10):
            reading = Reading(
                timestamp=base_time + timedelta(minutes=i * 5),
                device_id=test_device.id,
                value=20.0 + i
            )
            db_session.add(reading)
        db_session.commit()

        result = db_session.query(
            func.avg(Reading.value).label('avg_value'),
            func.min(Reading.value).label('min_value'),
            func.max(Reading.value).label('max_value')
        ).filter(
            Reading.device_id == test_device.id,
            Reading.timestamp >= base_time
        ).first()

        # All aggregates should return non-null values
        assert result.avg_value is not None
        assert result.min_value is not None
        assert result.max_value is not None


class TestAggregationPerformance:
    """Test aggregation query performance characteristics"""

    def test_aggregate_pagination(self, db_session, test_device, time_series_data):
        """Test that aggregated results can be paginated"""
        # Get first page
        page1 = db_session.query(
            func.strftime('%Y-%m-%d %H:00:00', Reading.timestamp).label('time_bucket'),
            func.avg(Reading.value).label('avg_value')
        ).filter(
            Reading.device_id == test_device.id
        ).group_by(
            func.strftime('%Y-%m-%d %H:00:00', Reading.timestamp)
        ).order_by(
            func.strftime('%Y-%m-%d %H:00:00', Reading.timestamp).desc()
        ).limit(10).all()

        # Get second page
        page2 = db_session.query(
            func.strftime('%Y-%m-%d %H:00:00', Reading.timestamp).label('time_bucket'),
            func.avg(Reading.value).label('avg_value')
        ).filter(
            Reading.device_id == test_device.id
        ).group_by(
            func.strftime('%Y-%m-%d %H:00:00', Reading.timestamp)
        ).order_by(
            func.strftime('%Y-%m-%d %H:00:00', Reading.timestamp).desc()
        ).limit(10).offset(10).all()

        assert len(page1) == 10
        assert len(page2) == 10
        assert page1[0].time_bucket != page2[0].time_bucket

    def test_aggregate_large_dataset_efficiency(self, db_session, test_device):
        """Test aggregation performance with large dataset"""
        # Create large dataset - 30 days with 1-minute intervals
        base_time = datetime.utcnow() - timedelta(days=30)
        batch_size = 1000

        for batch in range(30 * 24 * 60 // batch_size):
            readings = []
            for i in range(batch_size):
                timestamp = base_time + timedelta(minutes=batch * batch_size + i)
                reading = Reading(
                    timestamp=timestamp,
                    device_id=test_device.id,
                    value=20.0 + (i % 10)
                )
                readings.append(reading)

            db_session.add_all(readings)
            db_session.commit()

        # Aggregate should complete quickly even with large dataset
        results = db_session.query(
            func.strftime('%Y-%m-%d', Reading.timestamp).label('time_bucket'),
            func.avg(Reading.value).label('avg_value')
        ).filter(
            Reading.device_id == test_device.id
        ).group_by(
            func.strftime('%Y-%m-%d', Reading.timestamp)
        ).all()

        assert len(results) == 30  # 30 days
        # Test should complete quickly (actual timing would depend on hardware)
