#!/usr/bin/env python3
"""
Modbus TCP Simulator for testing DDMS

This script simulates a Modbus TCP device with realistic sensor data.
It runs a Modbus TCP server on localhost that generates:
- Temperature readings (20-30°C with realistic fluctuations)
- Pressure readings (100-110 PSI)
- Flow rate readings (50-60 L/min)

Usage:
    python3 scripts/modbus_simulator.py [--port PORT] [--slave-id SLAVE_ID]

Options:
    --port PORT           TCP port (default: 5020)
    --slave-id SLAVE_ID   Modbus slave ID (default: 1)

Example DDMS Device Configuration:
    Device Name: Test Temperature Sensor
    Modbus IP: 127.0.0.1
    Modbus Port: 5020
    Slave ID: 1
    Register Address: 0
    Register Count: 2
    Unit: °C
    Sampling Interval: 5 seconds
"""

import argparse
import logging
import time
import math
import random
import struct
import threading

try:
    from pymodbus.server import StartTcpServer
    from pymodbus.datastore import (
        ModbusSequentialDataBlock,
        ModbusDeviceContext,
        ModbusServerContext
    )
except ImportError as e:
    print("Error: pymodbus 3.x is required but not installed")
    print("Please install: pip install 'pymodbus>=3.0'")
    print(f"Details: {e}")
    exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimulatedDevice:
    """Simulates realistic sensor readings"""

    def __init__(self):
        self.start_time = time.time()
        self.base_temp = 25.0  # Base temperature in Celsius
        self.base_pressure = 105.0  # Base pressure in PSI
        self.base_flow = 55.0  # Base flow rate in L/min

    def get_temperature(self) -> float:
        """
        Generate realistic temperature reading
        Returns temperature in Celsius (20-30°C range)
        """
        elapsed = time.time() - self.start_time
        # Sinusoidal variation + random noise
        variation = 3.0 * math.sin(elapsed / 30.0)  # Slow drift
        noise = random.uniform(-0.5, 0.5)  # Small random fluctuations
        return self.base_temp + variation + noise

    def get_pressure(self) -> float:
        """
        Generate realistic pressure reading
        Returns pressure in PSI (100-110 PSI range)
        """
        elapsed = time.time() - self.start_time
        variation = 4.0 * math.sin(elapsed / 45.0)
        noise = random.uniform(-0.3, 0.3)
        return self.base_pressure + variation + noise

    def get_flow_rate(self) -> float:
        """
        Generate realistic flow rate reading
        Returns flow rate in L/min (50-60 L/min range)
        """
        elapsed = time.time() - self.start_time
        variation = 3.0 * math.sin(elapsed / 20.0)
        noise = random.uniform(-0.8, 0.8)
        return self.base_flow + variation + noise

    def float_to_registers(self, value: float) -> tuple:
        """
        Convert float to two 16-bit Modbus registers (32-bit float)
        Uses IEEE 754 single precision format
        """
        # Pack float as 4 bytes
        bytes_val = struct.pack('>f', value)
        # Unpack as two 16-bit integers
        high, low = struct.unpack('>HH', bytes_val)
        return high, low


def update_registers_callback(context, slave_id):
    """Callback to continuously update simulated sensor values"""
    simulator = SimulatedDevice()

    def updater():
        while True:
            try:
                # Get simulated readings
                temp = simulator.get_temperature()
                pressure = simulator.get_pressure()
                flow = simulator.get_flow_rate()

                # Convert to register values
                temp_high, temp_low = simulator.float_to_registers(temp)
                pressure_high, pressure_low = simulator.float_to_registers(pressure)
                flow_high, flow_low = simulator.float_to_registers(flow)

                # Update holding registers
                # Registers 0-1: Temperature
                # Registers 2-3: Pressure
                # Registers 4-5: Flow Rate
                fx = 0x03  # Holding Registers
                address = 0x00

                values = [
                    temp_high, temp_low,      # Registers 0-1: Temperature
                    pressure_high, pressure_low,  # Registers 2-3: Pressure
                    flow_high, flow_low,      # Registers 4-5: Flow Rate
                ]

                context[slave_id].setValues(fx, address, values)

                # Log current values
                logger.info(
                    f"Updated values - Temp: {temp:.2f}°C, "
                    f"Pressure: {pressure:.2f} PSI, "
                    f"Flow: {flow:.2f} L/min"
                )

                # Update every 2 seconds
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error updating registers: {e}")
                time.sleep(2)

    updater_thread = threading.Thread(target=updater, daemon=True)
    updater_thread.start()


def run_server(port=5020, slave_id=1):
    """Start the Modbus TCP simulator server"""

    # Initialize data store with 100 registers
    # Holding registers (function code 3)
    store = ModbusDeviceContext(
        di=ModbusSequentialDataBlock(0, [0]*100),  # Discrete Inputs
        co=ModbusSequentialDataBlock(0, [0]*100),  # Coils
        hr=ModbusSequentialDataBlock(0, [0]*100),  # Holding Registers
        ir=ModbusSequentialDataBlock(0, [0]*100),  # Input Registers
    )

    # Create server context (pymodbus 3.x uses 'devices' parameter)
    context = ModbusServerContext(devices={slave_id: store}, single=False)

    # Start background updater
    update_registers_callback(context, slave_id)

    # Print startup information
    logger.info("=" * 70)
    logger.info("DDMS Modbus TCP Simulator Started")
    logger.info("=" * 70)
    logger.info(f"Listening on: 127.0.0.1:{port}")
    logger.info(f"Slave ID: {slave_id}")
    logger.info("")
    logger.info("Available Registers:")
    logger.info("  Registers 0-1:  Temperature (°C) - IEEE 754 float")
    logger.info("  Registers 2-3:  Pressure (PSI) - IEEE 754 float")
    logger.info("  Registers 4-5:  Flow Rate (L/min) - IEEE 754 float")
    logger.info("")
    logger.info("Example DDMS Configuration:")
    logger.info("  Device Name: Test Temperature Sensor")
    logger.info("  Modbus IP: 127.0.0.1")
    logger.info(f"  Modbus Port: {port}")
    logger.info(f"  Slave ID: {slave_id}")
    logger.info("  Register Address: 0")
    logger.info("  Register Count: 2")
    logger.info("  Unit: °C")
    logger.info("  Sampling Interval: 5")
    logger.info("")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 70)
    logger.info("")

    try:
        StartTcpServer(
            context=context,
            address=("127.0.0.1", port)
        )
    except KeyboardInterrupt:
        logger.info("\nShutting down simulator...")


def main():
    parser = argparse.ArgumentParser(
        description='Modbus TCP Simulator for DDMS testing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5020,
        help='TCP port to listen on (default: 5020)'
    )
    parser.add_argument(
        '--slave-id',
        type=int,
        default=1,
        help='Modbus slave ID (default: 1)'
    )

    args = parser.parse_args()

    # Validate port range
    if not (1 <= args.port <= 65535):
        parser.error("Port must be between 1 and 65535")

    # Validate slave ID range
    if not (1 <= args.slave_id <= 255):
        parser.error("Slave ID must be between 1 and 255")

    run_server(port=args.port, slave_id=args.slave_id)


if __name__ == '__main__':
    main()
