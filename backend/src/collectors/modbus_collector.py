"""
Modbus collector for reading data from Modbus TCP devices
"""
import asyncio
from typing import Optional
from datetime import datetime
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from src.utils.logging import get_logger

logger = get_logger(__name__)


class ModbusCollector:
    """
    Modbus TCP client for reading device data

    Handles connection management, register reading, and error handling
    """

    def __init__(
        self,
        host: str,
        port: int = 502,
        timeout: int = 10,
        retries: int = 3
    ):
        """
        Initialize Modbus collector

        Args:
            host: Modbus device IP address
            port: Modbus device port (default: 502)
            timeout: Connection timeout in seconds (default: 10)
            retries: Number of retry attempts on failure (default: 3)
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retries = retries
        self.client = AsyncModbusTcpClient(
            host=host,
            port=port,
            timeout=timeout
        )
        self._connected = False

    async def connect(self) -> bool:
        """
        Establish connection to Modbus device

        Returns:
            True if connection successful, False otherwise
        """
        try:
            await self.client.connect()
            self._connected = self.client.connected

            if self._connected:
                logger.info(f"Connected to Modbus device at {self.host}:{self.port}")
            else:
                logger.error(f"Failed to connect to Modbus device at {self.host}:{self.port}")

            return self._connected

        except Exception as e:
            logger.error(f"Exception connecting to Modbus device {self.host}:{self.port}: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        """Close connection to Modbus device"""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info(f"Disconnected from Modbus device at {self.host}:{self.port}")

    @property
    def is_connected(self) -> bool:
        """Check if currently connected"""
        return self._connected and self.client.connected

    async def read_holding_registers(
        self,
        slave_id: int,
        register: int,
        count: int = 1
    ) -> Optional[list[int]]:
        """
        Read holding registers from Modbus device

        Args:
            slave_id: Modbus slave ID
            register: Starting register address
            count: Number of registers to read (default: 1)

        Returns:
            List of register values, or None on error
        """
        if not self.is_connected:
            logger.warning(f"Not connected to {self.host}:{self.port}, attempting to connect...")
            if not await self.connect():
                return None

        for attempt in range(self.retries):
            try:
                result = await self.client.read_holding_registers(
                    address=register,
                    count=count,
                    slave=slave_id
                )

                if result.isError():
                    logger.error(
                        f"Modbus read error from {self.host}:{self.port} "
                        f"(slave={slave_id}, register={register}): {result}"
                    )

                    # Try to reconnect on error
                    if attempt < self.retries - 1:
                        logger.info(f"Attempting reconnection (attempt {attempt + 1}/{self.retries})")
                        await self.disconnect()
                        await asyncio.sleep(1)
                        if not await self.connect():
                            continue

                    continue

                # Success
                values = result.registers
                logger.debug(
                    f"Read {count} register(s) from {self.host}:{self.port} "
                    f"(slave={slave_id}, register={register}): {values}"
                )
                return values

            except ModbusException as e:
                logger.error(
                    f"Modbus exception reading from {self.host}:{self.port}: {e}"
                )
                if attempt < self.retries - 1:
                    await asyncio.sleep(1)
                continue

            except Exception as e:
                logger.error(
                    f"Unexpected error reading from {self.host}:{self.port}: {e}"
                )
                if attempt < self.retries - 1:
                    await asyncio.sleep(1)
                continue

        logger.error(
            f"Failed to read registers after {self.retries} attempts from {self.host}:{self.port}"
        )
        return None

    async def read_value(
        self,
        slave_id: int,
        register: int,
        count: int = 1,
        scaling_factor: float = 1.0
    ) -> Optional[float]:
        """
        Read and convert register value(s) to float

        Args:
            slave_id: Modbus slave ID
            register: Starting register address
            count: Number of registers to read (default: 1)
            scaling_factor: Factor to scale the raw value (default: 1.0)

        Returns:
            Scaled float value, or None on error
        """
        registers = await self.read_holding_registers(slave_id, register, count)

        if registers is None:
            return None

        # Convert register(s) to value
        # For single register: just the value
        # For multiple registers: combine them (implementation depends on device)
        if count == 1:
            raw_value = registers[0]
        else:
            # For multiple registers, this is a simple implementation
            # Real implementation may need to handle different data types
            raw_value = sum(registers)

        # Apply scaling
        return float(raw_value) * scaling_factor

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
