"""
Unit tests for Modbus collector
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.collectors.modbus_collector import ModbusCollector


class TestModbusCollectorInit:
    """Test ModbusCollector initialization"""

    def test_init_default_parameters(self):
        """Test collector initialization with default parameters"""
        collector = ModbusCollector(host="192.168.1.100")

        assert collector.host == "192.168.1.100"
        assert collector.port == 502
        assert collector.timeout == 10
        assert collector.retries == 3

    def test_init_custom_parameters(self):
        """Test collector initialization with custom parameters"""
        collector = ModbusCollector(
            host="10.0.0.50",
            port=5020,
            timeout=5,
            retries=5
        )

        assert collector.host == "10.0.0.50"
        assert collector.port == 5020
        assert collector.timeout == 5
        assert collector.retries == 5


class TestModbusCollectorConnect:
    """Test ModbusCollector connect method"""

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful connection"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_client.connected = True
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100")
            result = await collector.connect()

            assert result is True
            mock_client.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test connection failure"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_client.connected = False
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100")
            result = await collector.connect()

            assert result is False


class TestModbusCollectorReadHoldingRegisters:
    """Test ModbusCollector read_holding_registers method"""

    @pytest.mark.asyncio
    async def test_read_success_first_attempt(self):
        """Test successful read on first attempt"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_response = Mock()
            mock_response.isError.return_value = False
            mock_response.registers = [100, 200]

            mock_client = AsyncMock()
            mock_client.read_holding_registers = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100")
            result = await collector.read_holding_registers(
                slave_id=1,
                register=0,
                count=2
            )

            assert result == [100, 200]
            assert mock_client.read_holding_registers.call_count == 1

    @pytest.mark.asyncio
    async def test_read_retry_then_success(self):
        """Test read succeeds after retry"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            # First call returns error, second call succeeds
            mock_error_response = Mock()
            mock_error_response.isError.return_value = True

            mock_success_response = Mock()
            mock_success_response.isError.return_value = False
            mock_success_response.registers = [300]

            mock_client = AsyncMock()
            mock_client.read_holding_registers = AsyncMock(
                side_effect=[mock_error_response, mock_success_response]
            )
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100", retries=3)
            result = await collector.read_holding_registers(
                slave_id=1,
                register=0,
                count=1
            )

            assert result == [300]
            assert mock_client.read_holding_registers.call_count == 2

    @pytest.mark.asyncio
    async def test_read_all_retries_fail(self):
        """Test read fails after all retries exhausted"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_error_response = Mock()
            mock_error_response.isError.return_value = True

            mock_client = AsyncMock()
            mock_client.read_holding_registers = AsyncMock(return_value=mock_error_response)
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100", retries=3)
            result = await collector.read_holding_registers(
                slave_id=1,
                register=0,
                count=1
            )

            assert result is None
            assert mock_client.read_holding_registers.call_count == 3

    @pytest.mark.asyncio
    async def test_read_with_exception(self):
        """Test read with exception during communication"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.read_holding_registers = AsyncMock(
                side_effect=Exception("Connection lost")
            )
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100", retries=2)
            result = await collector.read_holding_registers(
                slave_id=1,
                register=0,
                count=1
            )

            assert result is None
            assert mock_client.read_holding_registers.call_count == 2


class TestModbusCollectorReadValue:
    """Test ModbusCollector read_value method"""

    @pytest.mark.asyncio
    async def test_read_value_success(self):
        """Test successful value read and scaling"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_response = Mock()
            mock_response.isError.return_value = False
            mock_response.registers = [1000]  # Raw value

            mock_client = AsyncMock()
            mock_client.read_holding_registers = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100")
            result = await collector.read_value(
                slave_id=1,
                register=0,
                count=1,
                scaling_factor=0.1  # Scale to 100.0
            )

            assert result == 100.0

    @pytest.mark.asyncio
    async def test_read_value_no_scaling(self):
        """Test value read without scaling"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_response = Mock()
            mock_response.isError.return_value = False
            mock_response.registers = [250]

            mock_client = AsyncMock()
            mock_client.read_holding_registers = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100")
            result = await collector.read_value(
                slave_id=1,
                register=0,
                count=1,
                scaling_factor=1.0  # No scaling
            )

            assert result == 250.0

    @pytest.mark.asyncio
    async def test_read_value_multiple_registers(self):
        """Test reading multiple registers"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_response = Mock()
            mock_response.isError.return_value = False
            mock_response.registers = [100, 200]  # Two registers

            mock_client = AsyncMock()
            mock_client.read_holding_registers = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100")
            result = await collector.read_value(
                slave_id=1,
                register=0,
                count=2,
                scaling_factor=1.0
            )

            # Should return first register value
            assert result == 100.0

    @pytest.mark.asyncio
    async def test_read_value_failure(self):
        """Test value read failure"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_error_response = Mock()
            mock_error_response.isError.return_value = True

            mock_client = AsyncMock()
            mock_client.read_holding_registers = AsyncMock(return_value=mock_error_response)
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100", retries=1)
            result = await collector.read_value(
                slave_id=1,
                register=0,
                count=1
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_read_value_negative_scaling(self):
        """Test value read with negative scaling factor"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_response = Mock()
            mock_response.isError.return_value = False
            mock_response.registers = [1000]

            mock_client = AsyncMock()
            mock_client.read_holding_registers = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100")
            result = await collector.read_value(
                slave_id=1,
                register=0,
                count=1,
                scaling_factor=-0.1  # Negative scaling
            )

            assert result == -100.0


class TestModbusCollectorClose:
    """Test ModbusCollector close method"""

    @pytest.mark.asyncio
    async def test_close_success(self):
        """Test successful connection close"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100")
            await collector.close()

            mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_with_exception(self):
        """Test close handles exceptions gracefully"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.close = AsyncMock(side_effect=Exception("Close error"))
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100")
            # Should not raise exception
            await collector.close()

            mock_client.close.assert_called_once()


class TestModbusCollectorIntegration:
    """Integration-style tests for ModbusCollector workflow"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete connect-read-close workflow"""
        with patch('src.collectors.modbus_collector.AsyncModbusTcpClient') as mock_client_class:
            mock_response = Mock()
            mock_response.isError.return_value = False
            mock_response.registers = [2500]

            mock_client = AsyncMock()
            mock_client.connect = AsyncMock()
            mock_client.connected = True
            mock_client.read_holding_registers = AsyncMock(return_value=mock_response)
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            collector = ModbusCollector(host="192.168.1.100")

            # Connect
            connected = await collector.connect()
            assert connected is True

            # Read value
            value = await collector.read_value(slave_id=1, register=0, count=1, scaling_factor=0.1)
            assert value == 250.0

            # Close
            await collector.close()

            mock_client.connect.assert_called_once()
            mock_client.read_holding_registers.assert_called_once()
            mock_client.close.assert_called_once()
