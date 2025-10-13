"""
Pytest configuration and fixtures for testing
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.db.base import Base

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine"""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a test database session"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "password": "Test123!@#",
        "role": "admin",
        "language_preference": "en"
    }


@pytest.fixture
def sample_device_data():
    """Sample device data for testing"""
    return {
        "name": "Test Device",
        "modbus_ip": "192.168.1.100",
        "modbus_port": 502,
        "modbus_slave_id": 1,
        "modbus_register": 0,
        "modbus_register_count": 1,
        "unit": "°C",
        "sampling_interval": 10,
        "threshold_warning_lower": 0.0,
        "threshold_warning_upper": 50.0,
        "threshold_critical_lower": -10.0,
        "threshold_critical_upper": 80.0,
        "retention_days": 90
    }
