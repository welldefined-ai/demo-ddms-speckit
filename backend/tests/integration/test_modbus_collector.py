"""
Integration tests for Modbus collector
Tests actual Modbus connection behavior with mocked network layer
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
import asyncio

from src.collectors.modbus_collector import ModbusCollector


class TestModbusCollectorIntegration:
    """Integration tests for ModbusCollector (T058)"""

    @pytest.mark.asyncio
    async def test_connection_validation_success(self):
        """Test successful connection validation workflow"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            # Setup mock client
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_client.connected = True

            mock_response = Mock()
            mock_response.isError.return_value = False
            mock_response.registers = [250]

            mock_client.read_holding_registers = AsyncMock(return_value=mock_response)
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            # Execute full connection test workflow
            collector = ModbusCollector(
                host="192.168.1.100",
                port=502,
                timeout=10,
                retries=3
            )

            # Step 1: Connect
            connected = await collector.connect()
            assert connected is True

            # Step 2: Read value to validate connection
            value = await collector.read_value(
                slave_id=1,
                register=0,
                count=1,
                scaling_factor=1.0
            )
            assert value == 250.0

            # Step 3: Close connection
            await collector.close()

            # Verify all steps were executed
            mock_client.connect.assert_called_once()
            mock_client.read_holding_registers.assert_called_once()
            mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_validation_connection_refused(self):
        """Test connection validation when connection is refused"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_client.connected = False  # Connection refused
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100")

            # Connect should fail
            connected = await collector.connect()
            assert connected is False

            # Should not attempt to read
            await collector.close()
            mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_validation_network_timeout(self):
        """Test connection validation with network timeout"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock(side_effect=asyncio.TimeoutError("Connection timeout"))
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100", timeout=5)

            # Connection should raise timeout
            with pytest.raises(asyncio.TimeoutError):
                await collector.connect()

    @pytest.mark.asyncio
    async def test_connection_validation_slave_not_responding(self):
        """Test when device connects but slave doesn't respond"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_error_response = Mock()
            mock_error_response.isError.return_value = True

            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_client.connected = True
            mock_client.read_holding_registers = AsyncMock(return_value=mock_error_response)
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100", retries=3)

            connected = await collector.connect()
            assert connected is True

            # Reading should fail after all retries
            value = await collector.read_value(slave_id=1, register=0, count=1)
            assert value is None

            # Verify all retries were attempted
            assert mock_client.read_holding_registers.call_count == 3

            await collector.close()

    @pytest.mark.asyncio
    async def test_connection_validation_intermittent_failure(self):
        """Test connection validation with intermittent failures"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            # First read fails, second succeeds
            mock_error_response = Mock()
            mock_error_response.isError.return_value = True

            mock_success_response = Mock()
            mock_success_response.isError.return_value = False
            mock_success_response.registers = [300]

            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_client.connected = True
            mock_client.read_holding_registers = AsyncMock(
                side_effect=[mock_error_response, mock_success_response]
            )
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100", retries=3)

            connected = await collector.connect()
            assert connected is True

            # Should succeed on second attempt
            value = await collector.read_value(slave_id=1, register=0, count=1)
            assert value == 300.0

            # Verify retry mechanism worked
            assert mock_client.read_holding_registers.call_count == 2

            await collector.close()

    @pytest.mark.asyncio
    async def test_connection_validation_wrong_slave_id(self):
        """Test connection validation with wrong slave ID"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_error_response = Mock()
            mock_error_response.isError.return_value = True

            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_client.connected = True
            mock_client.read_holding_registers = AsyncMock(return_value=mock_error_response)
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100", retries=2)

            connected = await collector.connect()
            assert connected is True

            # Reading with wrong slave ID should fail
            value = await collector.read_value(slave_id=99, register=0, count=1)
            assert value is None

            await collector.close()

    @pytest.mark.asyncio
    async def test_connection_validation_invalid_register(self):
        """Test connection validation with invalid register address"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_error_response = Mock()
            mock_error_response.isError.return_value = True

            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_client.connected = True
            mock_client.read_holding_registers = AsyncMock(return_value=mock_error_response)
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100", retries=2)

            connected = await collector.connect()
            assert connected is True

            # Reading invalid register should fail
            value = await collector.read_value(slave_id=1, register=99999, count=1)
            assert value is None

            await collector.close()

    @pytest.mark.asyncio
    async def test_concurrent_reads_from_same_collector(self):
        """Test multiple concurrent reads from the same collector"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_response1 = Mock()
            mock_response1.isError.return_value = False
            mock_response1.registers = [100]

            mock_response2 = Mock()
            mock_response2.isError.return_value = False
            mock_response2.registers = [200]

            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_client.connected = True
            mock_client.read_holding_registers = AsyncMock(
                side_effect=[mock_response1, mock_response2]
            )
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100")

            await collector.connect()

            # Perform concurrent reads
            task1 = collector.read_value(slave_id=1, register=0, count=1)
            task2 = collector.read_value(slave_id=1, register=1, count=1)

            results = await asyncio.gather(task1, task2)

            assert results[0] == 100.0
            assert results[1] == 200.0
            assert mock_client.read_holding_registers.call_count == 2

            await collector.close()

    @pytest.mark.asyncio
    async def test_connection_validation_with_different_timeouts(self):
        """Test connection validation with various timeout settings"""
        test_cases = [
            (5, True),   # Short timeout, should succeed
            (10, True),  # Default timeout, should succeed
            (30, True),  # Long timeout, should succeed
        ]

        for timeout, expected_success in test_cases:
            with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
                mock_response = Mock()
                mock_response.isError.return_value = False
                mock_response.registers = [150]

                mock_client = AsyncMock()
                mock_client.connect = AsyncMock()
                mock_client.connected = True
                mock_client.read_holding_registers = AsyncMock(return_value=mock_response)
                mock_client.close = AsyncMock()
                mock_client_class.return_value = mock_client

                collector = ModbusCollector(host="192.168.1.100", timeout=timeout)

                connected = await collector.connect()
                assert connected is expected_success

                if expected_success:
                    value = await collector.read_value(slave_id=1, register=0, count=1)
                    assert value == 150.0

                await collector.close()

    @pytest.mark.asyncio
    async def test_connection_cleanup_on_error(self):
        """Test that connection is properly cleaned up on error"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_client.connected = True
            mock_client.read_holding_registers = AsyncMock(
                side_effect=Exception("Unexpected error")
            )
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100", retries=2)

            await collector.connect()

            # Reading should fail
            value = await collector.read_value(slave_id=1, register=0, count=1)
            assert value is None

            # Ensure connection can still be closed
            await collector.close()
            mock_client.close.assert_called_once()
