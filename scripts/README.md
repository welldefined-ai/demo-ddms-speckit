# DDMS Testing Scripts

## Modbus Device Simulator

### Overview

The `modbus_simulator.py` script simulates a Modbus TCP device for testing DDMS without physical hardware. It generates realistic sensor data for:
- **Temperature** (20-30°C with gradual drift and noise)
- **Pressure** (100-110 PSI)
- **Flow Rate** (50-60 L/min)

### Prerequisites

Install pymodbus:
```bash
pip install pymodbus
```

Or if using the backend virtual environment:
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install pymodbus
```

### Quick Start

1. **Start the simulator:**
   ```bash
   python3 scripts/modbus_simulator.py
   ```

   The simulator will start on `127.0.0.1:5020` with slave ID `1`.

2. **Access DDMS frontend:**
   Navigate to `http://localhost:3000/devices`

3. **Add a test device with these settings:**

   **Basic Information:**
   - Device Name: `Test Temperature Sensor`
   - Unit of Measurement: `°C`
   - Sampling Interval: `5` seconds

   **Modbus Configuration:**
   - Modbus IP Address: `127.0.0.1`
   - Modbus Port: `5020`
   - Slave ID: `1`
   - Register Address: `0`
   - Register Count: `2`

   **Alert Thresholds (optional):**
   - Warning Lower: `22`
   - Warning Upper: `28`
   - Critical Lower: `20`
   - Critical Upper: `30`

   **Data Retention:**
   - Retention Days: `30`

4. **Test the connection:**
   Click the "Test Connection" button - you should see a success message.

5. **View real-time data:**
   Go to the Dashboard to see live temperature readings updating every 5 seconds.

6. **View historical data:**
   After collecting some data, go to Historical Data page to see charts and export data.

### Advanced Usage

#### Custom Port and Slave ID

Run the simulator on a different port or slave ID:

```bash
# Custom port
python3 scripts/modbus_simulator.py --port 5021

# Custom slave ID
python3 scripts/modbus_simulator.py --slave-id 2

# Both
python3 scripts/modbus_simulator.py --port 5021 --slave-id 2
```

#### Multiple Simulated Devices

Run multiple simulators on different ports to test multiple devices:

**Terminal 1:**
```bash
python3 scripts/modbus_simulator.py --port 5020
```

**Terminal 2:**
```bash
python3 scripts/modbus_simulator.py --port 5021
```

Then add two devices in DDMS with:
- Device 1: `127.0.0.1:5020`
- Device 2: `127.0.0.1:5021`

#### Testing Different Register Addresses

The simulator provides data at different register addresses:

| Registers | Data Type | Unit | Description |
|-----------|-----------|------|-------------|
| 0-1 | Float | °C | Temperature |
| 2-3 | Float | PSI | Pressure |
| 4-5 | Float | L/min | Flow Rate |

**Example configurations:**

**Temperature Device:**
- Register Address: `0`
- Register Count: `2`
- Unit: `°C`

**Pressure Device:**
- Register Address: `2`
- Register Count: `2`
- Unit: `PSI`

**Flow Rate Device:**
- Register Address: `4`
- Register Count: `2`
- Unit: `L/min`

### Testing Scenarios

#### 1. Basic Monitoring
- Add device with 5-second sampling interval
- Watch real-time updates on dashboard
- Verify values are in expected range (20-30°C)

#### 2. Threshold Alerts
- Set warning thresholds: 22-28°C
- Set critical thresholds: 20-30°C
- Observe when readings trigger warnings/alerts

#### 3. Historical Data
- Let device collect data for 5-10 minutes
- Go to Historical Data page
- Select device and time range
- Export data as CSV

#### 4. Device Groups
- Create multiple simulated devices
- Group them together
- View aggregate readings on Group Dashboard
- Export group data

#### 5. Connection Resilience
- Start device monitoring
- Stop simulator (Ctrl+C)
- Observe connection error handling in DDMS
- Restart simulator
- Verify automatic reconnection

### Troubleshooting

**Port already in use:**
```
Error: [Errno 48] Address already in use
```
Solution: Either stop the other process or use a different port with `--port 5021`

**Connection refused in DDMS:**
- Ensure simulator is running
- Verify IP is `127.0.0.1` (not `localhost` on some systems)
- Check port number matches
- Check firewall settings

**No data appearing:**
- Verify register address is correct (0 for temperature)
- Verify register count is 2
- Check backend logs: `tail -f logs/backend.log`
- Check simulator output for errors

**Values seem wrong:**
- The simulator uses IEEE 754 32-bit float format (2 registers)
- Verify Register Count is `2`, not `1`
- Check backend is correctly decoding the float value

### Data Format

The simulator stores floating-point values using IEEE 754 single precision format across two consecutive 16-bit Modbus registers:

```
Register N:   High 16 bits of float
Register N+1: Low 16 bits of float
```

Example: Temperature value `25.5°C`
- Converted to IEEE 754: `0x41CC0000`
- Register 0: `0x41CC` (high bytes)
- Register 1: `0x0000` (low bytes)

### Stopping the Simulator

Press `Ctrl+C` in the terminal running the simulator to stop it gracefully.
