"""
Unit tests for Configuration model
"""
import pytest
import uuid
from src.models.configuration import Configuration


class TestConfigurationModel:
    """Test Configuration model functionality"""

    def test_create_configuration(self, db_session):
        """Test creating configuration"""
        config = Configuration(
            id=uuid.uuid4(),
            system_name="Test DDMS",
            data_retention_days_default=90,
            backup_enabled=True,
            backup_schedule="0 2 * * *"
        )

        db_session.add(config)
        db_session.commit()

        assert config.id is not None
        assert config.system_name == "Test DDMS"
        assert config.data_retention_days_default == 90
        assert config.backup_enabled is True
        assert config.backup_schedule == "0 2 * * *"

    def test_configuration_defaults(self, db_session):
        """Test configuration default values"""
        config = Configuration(id=uuid.uuid4())

        db_session.add(config)
        db_session.commit()

        assert config.system_name == "DDMS - Device Data Monitoring System"
        assert config.data_retention_days_default == 90
        assert config.backup_enabled is True
        assert config.backup_schedule == "0 2 * * *"

    def test_configuration_repr(self, db_session):
        """Test configuration string representation"""
        config = Configuration(
            id=uuid.uuid4(),
            system_name="Test DDMS"
        )

        db_session.add(config)
        db_session.commit()

        repr_str = repr(config)
        assert "Configuration" in repr_str
        assert "Test DDMS" in repr_str
