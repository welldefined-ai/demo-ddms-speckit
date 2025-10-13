# Feature Specification: DDMS Web Application

**Feature Branch**: `001-ddms-web-application`  
**Created**: 2025-10-10  
**Status**: Draft  
**Input**: User description: "refer to requirements.md for more info on requirements for this demo monitor web application"

## Clarifications

### Session 2025-10-10

- Q: How should devices be uniquely identified in the system? → A: By user-assigned device name (names must be unique across system)
- Q: What is the Modbus device reconnection policy when connection is lost? → A: Retry every 60 seconds indefinitely with admin notification after 3 consecutive failures
- Q: How should the system notify admins of device connection failures? → A: In-app notification banner only (visible when logged in)
- Q: What is the default data retention period for device readings? → A: 90 days (quarterly retention for trend analysis)
- Q: What is the default sampling interval for device data collection? → A: 10 seconds (high-frequency monitoring, ~8,640 readings/device/day)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-Time Device Monitoring Dashboard (Priority: P1)

An operator logs into DDMS and immediately sees live readings from all connected industrial devices displayed with visual indicators showing normal, warning, or critical status. Charts auto-refresh at configured intervals, with threshold lines overlayed to provide instant awareness of device conditions.

**Why this priority**: This is the core value proposition - operators need real-time visibility into device status for safety and operational decision-making. Without this, the system provides no value.

**Independent Test**: Can be fully tested by configuring one device and verifying that current readings display with correct color-coded indicators, auto-refresh works, and threshold violations trigger visual warnings.

**Acceptance Scenarios**:

1. **Given** operator is logged in and devices are connected, **When** they view the monitoring dashboard, **Then** current readings from all devices display with timestamps
2. **Given** a device reading is within normal range, **When** operator views the dashboard, **Then** the device shows green/normal indicator
3. **Given** a device reading approaches warning threshold, **When** operator views the dashboard, **Then** the device shows yellow warning indicator
4. **Given** a device reading exceeds critical threshold, **When** operator views the dashboard, **Then** the device shows red critical indicator with visual prominence
5. **Given** dashboard is displaying live data, **When** configured sampling interval elapses, **Then** charts auto-refresh with new readings without page reload
6. **Given** operator hovers over a chart datapoint, **When** tooltip appears, **Then** exact value, unit, and timestamp are shown

---

### User Story 2 - Device Configuration and Threshold Management (Priority: P2)

An admin configures new Modbus devices by specifying connection parameters, naming the device, setting sampling intervals, and defining warning/critical thresholds. The system validates configuration, connects to the device, and begins collecting data.

**Why this priority**: Devices must be configured before monitoring can occur. This is essential infrastructure but depends on the monitoring dashboard to show value.

**Independent Test**: Can be tested by adding a single Modbus device through the configuration interface, verifying connection succeeds, and confirming data collection begins per configured interval.

**Acceptance Scenarios**:

1. **Given** admin user is logged in, **When** they navigate to device configuration, **Then** they can add a new device
2. **Given** admin is adding a device, **When** they specify Modbus TCP/IP parameters (IP, port, register addresses), **Then** system validates and tests connection
3. **Given** admin is configuring device, **When** they set device name, units (°C, bar, RPM, %), and sampling interval, **Then** system saves configuration
4. **Given** admin is setting thresholds, **When** they specify warning and critical upper/lower limits with hysteresis, **Then** system applies thresholds to monitoring
5. **Given** admin is viewing device list, **When** checking device status, **Then** online/offline status and last successful reading timestamp display
6. **Given** admin needs to remove a device, **When** they delete it, **Then** system prompts to keep or delete historical data and completes deletion

---

### User Story 3 - User Account Management (Priority: P3)

The system owner creates and manages user accounts with different roles (owner, admin, read-only), enabling secure multi-user access with appropriate permissions for operational needs.

**Why this priority**: Multi-user access is important for operational environments but system can function with single owner account initially for MVP.

**Independent Test**: Can be tested by owner logging in, creating accounts for each role type, verifying role-based access restrictions, and confirming password changes work.

**Acceptance Scenarios**:

1. **Given** system is newly installed, **When** owner accesses for first time, **Then** default owner account exists with credentials provided in documentation
2. **Given** owner is logged in, **When** they navigate to user management, **Then** they can create admin and read-only user accounts
3. **Given** owner creates new user, **When** they specify username, password, and role, **Then** account is created and user can log in
4. **Given** owner or user needs to change password, **When** they access account settings, **Then** they can update their password
5. **Given** admin user is logged in, **When** they attempt device configuration, **Then** they have full access
6. **Given** read-only user is logged in, **When** they attempt device configuration, **Then** access is denied and only viewing is permitted
7. **Given** owner needs to remove user, **When** they delete account (excluding owner), **Then** user is removed and cannot log in

---

### User Story 4 - Historical Data Analysis and Export (Priority: P4)

An operator analyzes historical trends by selecting custom time ranges, zooming into specific periods, and exporting data to CSV for external analysis or reporting.

**Why this priority**: Historical analysis is valuable for identifying trends and patterns but system delivers immediate value with real-time monitoring alone.

**Independent Test**: Can be tested by accumulating historical data for one device, selecting various time ranges, verifying zoom functionality, and exporting to CSV with correct data format.

**Acceptance Scenarios**:

1. **Given** operator selects a device with historical data, **When** they navigate to historical view, **Then** trend chart displays with selectable time ranges
2. **Given** operator is viewing historical trends, **When** they select time range (last hour, 24 hours, week, custom), **Then** chart updates to show selected period
3. **Given** operator is viewing historical chart, **When** they zoom into a specific time period, **Then** chart displays detailed view of that period
4. **Given** historical chart is displayed, **When** threshold lines are overlayed, **Then** operator can see when readings crossed thresholds historically
5. **Given** operator needs data for external analysis, **When** they export to CSV, **Then** file downloads with timestamps, values, and units in standard format

---

### User Story 5 - Device Grouping and Group Dashboards (Priority: P5)

An admin organizes devices into logical groups (by production line, building area, device type, etc.) and views group-level dashboards showing aggregated status and trends for all devices in the group.

**Why this priority**: Grouping enhances usability for large deployments but system is fully functional monitoring individual devices without grouping.

**Independent Test**: Can be tested by creating a group, assigning multiple devices to it, and verifying group dashboard displays all device readings with group-level alert summary.

**Acceptance Scenarios**:

1. **Given** admin has multiple configured devices, **When** they create a new group with a name, **Then** empty group is created
2. **Given** admin is managing groups, **When** they assign devices to a group, **Then** devices can belong to multiple groups simultaneously
3. **Given** operator views a group dashboard, **When** accessing the group, **Then** real-time readings for all group devices display together
4. **Given** operator is viewing group dashboard, **When** checking group status, **Then** group-level alert summary shows count of normal/warning/critical devices
5. **Given** operator needs group historical data, **When** they export group data, **Then** CSV includes all devices in the group with timestamp alignment
6. **Given** admin needs to reorganize, **When** they rename or delete groups, **Then** changes apply without affecting device configurations

---

### Edge Cases

- **Network interruption**: What happens when connection to a Modbus device is lost during operation? System marks device offline, shows last successful reading timestamp, displays communication error indicator, and retries connection every 60 seconds indefinitely. Admin users receive notification after 3 consecutive connection failures.

- **Threshold flapping**: How does system handle readings oscillating around threshold boundary? Hysteresis configuration prevents rapid alert state changes by requiring reading to cross threshold plus hysteresis value before changing state.

- **Concurrent user modifications**: What happens when multiple admins modify same device configuration simultaneously? Last write wins with transaction safety; system logs all configuration changes with user and timestamp for audit trail.

- **Data retention overflow**: What happens when storage approaches capacity? System automatically deletes oldest data per configured retention period (default 90 days); admin receives in-app warning banner before automatic cleanup; manual export available before deletion.

- **Browser compatibility**: How does system handle older browsers? System detects browser version on login and displays warning if unsupported; graceful degradation for non-critical animations while maintaining core monitoring functionality.

- **Tablet touch interactions**: How do chart interactions work on tablets? Touch-friendly controls with appropriate hit targets; pinch-to-zoom for historical charts; swipe for time range navigation; long-press for tooltips.

- **Time zone handling**: How are timestamps displayed across different local times? All timestamps stored in UTC in database; displayed in server local time with timezone indicator; future enhancement could support user-specific timezone preference.

- **Device with no data yet**: How is newly configured device displayed before first reading? Device shows "waiting for data" status; chart displays empty state with message "No data available yet - waiting for first reading at [next sampling time]".

## Requirements *(mandatory)*

### Functional Requirements

#### Authentication & Authorization

- **FR-001**: System MUST provide default owner account with username and password on initial setup
- **FR-002**: System MUST allow owner to change their own username and password
- **FR-003**: System MUST allow owner to create admin and read-only user accounts
- **FR-004**: System MUST allow owner to delete any user account except the owner account
- **FR-005**: System MUST enforce role-based access control with three roles: owner (full system access and user management), admin (full device configuration and monitoring), read-only (view-only dashboard access)
- **FR-006**: System MUST require authentication for all web access and maintain session security

#### Real-Time Monitoring

- **FR-007**: System MUST display current readings from all connected monitoring devices on dashboard
- **FR-008**: System MUST show device data in chart formats including line charts and gauges
- **FR-009**: System MUST auto-refresh data at configured sampling intervals without page reload
- **FR-010**: System MUST support displaying multiple devices simultaneously
- **FR-011**: System MUST display yellow warning indicator when reading approaches threshold (within hysteresis range)
- **FR-012**: System MUST display red critical indicator when reading exceeds upper threshold or falls below lower threshold
- **FR-013**: System MUST show visual warning indicators on both charts and device lists
- **FR-014**: System MUST overlay threshold lines (warning and critical) on trend charts
- **FR-015**: System MUST display current reading value, units, and threshold values on charts
- **FR-016**: System MUST show color-coded regions (normal/warning/critical) on charts
- **FR-017**: System MUST provide hover tooltips showing exact values, units, and timestamps

#### Historical Data

- **FR-018**: System MUST allow users to view historical trend curves for any device reading
- **FR-019**: System MUST allow users to customize time range for historical data (last hour, 24 hours, week, custom date range)
- **FR-020**: System MUST allow users to zoom in/out on specific time periods in historical charts
- **FR-021**: System MUST allow users to export historical data to CSV files with timestamps, values, and units
- **FR-022**: System MUST display threshold lines on historical trend charts for context

#### Device Configuration

- **FR-023**: System MUST allow admin and owner users to add new monitoring devices
- **FR-024**: System MUST allow configuration of Modbus TCP/IP connection parameters (IP address, port, register addresses, data types)
- **FR-025**: System MUST allow setting device name, description, and reading units (°C, bar, RPM, %, etc.)
- **FR-025a**: System MUST enforce unique device names across the system and prevent creation of devices with duplicate names
- **FR-026**: System MUST allow setting sampling interval per device (frequency of data collection, default: 10 seconds)
- **FR-027**: System MUST allow setting data retention period per device (default: 90 days)
- **FR-028**: System MUST allow setting upper threshold limits (warning and critical levels)
- **FR-029**: System MUST allow setting lower threshold limits (warning and critical levels)
- **FR-030**: System MUST allow setting hysteresis values to prevent alarm flapping
- **FR-031**: System MUST allow admin and owner users to delete devices with option to keep or delete historical data
- **FR-032**: System MUST display device connection status (online/offline) in real-time
- **FR-033**: System MUST display last successful reading timestamp for each device
- **FR-034**: System MUST display communication error indicators for devices that fail to respond
- **FR-034a**: System MUST automatically retry connection to offline devices every 60 seconds indefinitely
- **FR-034b**: System MUST display in-app notification banner to admin and owner users after 3 consecutive connection failures for any device (banner visible when user is logged in)

#### Device Grouping

- **FR-035**: System MUST allow admin and owner users to create logical groups of devices
- **FR-036**: System MUST allow assigning devices to one or more groups simultaneously
- **FR-037**: System MUST allow admin and owner users to rename and delete groups
- **FR-038**: System MUST provide group-level real-time monitoring dashboard showing all devices in group
- **FR-039**: System MUST provide historical trend charts aggregated for group
- **FR-040**: System MUST display group-level alert summary (count of devices in normal/warning/critical states)
- **FR-041**: System MUST allow CSV export for all devices in a group with timestamp-aligned data

#### User Interface

- **FR-047**: System MUST provide clean, modern interface design with professional appearance suitable for industrial environments
- **FR-048**: System MUST provide intuitive navigation and workflows
- **FR-049**: System MUST provide smooth transitions between views and animated chart updates
- **FR-050**: System MUST display loading indicators for asynchronous operations
- **FR-051**: System MUST provide responsive feedback for user actions with hover and focus effects
- **FR-052**: System MUST ensure high contrast between text and backgrounds for readability
- **FR-053**: System MUST provide clear visual hierarchy
- **FR-054**: System MUST use readable fonts at typical viewing distances
- **FR-055**: System MUST provide touch-friendly controls with appropriate hit targets for tablet access
- **FR-055a**: System MUST display in-app notification banners for critical system events (such as device connection failures) visible to admin and owner users when logged in

#### Data Persistence

- **FR-056**: System MUST store all configuration data persistently on server
- **FR-057**: System MUST store time-series data in database
- **FR-058**: System MUST provide automatic database backups on configurable schedule
- **FR-059**: System MUST enforce configured retention period per device and automatically clean up old data
- **FR-060**: System MUST allow manual data export before automatic deletion
- **FR-061**: System MUST persist data across server restarts
- **FR-062**: System MUST ensure transaction safety for configuration changes
- **FR-063**: System MUST provide error recovery mechanisms for data operations

#### Protocol Support

- **FR-064**: System MUST support Modbus TCP/IP protocol
- **FR-065**: System MUST support Modbus RTU over serial (optional future enhancement)
- **FR-066**: System MUST allow configurable register addresses for Modbus devices
- **FR-067**: System MUST allow configurable data types (INT16, UINT16, INT32, FLOAT32, etc.) for Modbus devices
- **FR-068**: System MUST support common industrial PLCs and sensors using standard Modbus protocol

#### Deployment

- **FR-069**: System MUST be deployable on customer's on-premises server (intranet deployment)
- **FR-070**: System MUST be accessible via web browser from internal network without requiring external internet connection
- **FR-071**: System MUST support modern web browsers including Chrome, Firefox, Edge, and Safari
- **FR-072**: System MUST provide responsive design for desktop and tablet access

### Key Entities

- **User**: Represents a system user with username, password (hashed), role (owner/admin/read-only), and account creation timestamp. Owner has full privileges, admin can configure devices, read-only can only view data.

- **Device**: Represents a monitoring device uniquely identified by its user-assigned device name (must be unique across system). Contains connection parameters (Modbus settings), description, reading units, sampling interval (default 10 seconds), retention period (default 90 days), threshold limits (warning/critical upper/lower), hysteresis values, connection status, last reading timestamp. Devices collect time-series data at configured intervals.

- **Reading**: Represents a time-series data point with timestamp, device reference, measured value, unit, and quality indicator (good/bad/uncertain). Readings are collected per device sampling interval and stored according to retention policy.

- **Threshold**: Represents alert boundaries with warning and critical levels for both upper and lower limits, plus hysteresis values. Thresholds trigger visual indicators when readings cross boundaries.

- **Group**: Represents a logical collection of devices with group name and description. Devices can belong to multiple groups. Groups enable aggregate monitoring and reporting.

- **Configuration**: Represents system-level settings including backup schedule, default retention period (90 days), language options, and session timeout values.

### Assumptions

- **Network Environment**: System assumes stable internal network connectivity between server and Modbus devices; temporary network issues handled with reconnection logic.

- **Modbus Standard Compliance**: Assumes industrial devices follow standard Modbus TCP/IP or RTU protocol specifications; proprietary protocol extensions not supported.

- **Browser Requirements**: Assumes users access system with modern browsers (released within last 2 years); older browser versions show compatibility warning.

- **Time Synchronization**: Assumes server has accurate system time (NTP recommended); timestamp accuracy critical for trend analysis.

- **Single Installation Per Site**: System designed for single-server deployment per factory/coalmine site; multi-site deployments require multiple installations.

- **Data Volume**: System optimized for up to 1000 devices with 10-second default sampling interval (~8,640 readings/device/day); larger deployments or higher frequencies may require infrastructure scaling.

- **User Training**: Assumes basic familiarity with web applications; comprehensive user documentation provided for device configuration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can view real-time device status for all connected devices within 3 seconds of dashboard load
- **SC-002**: System automatically refreshes device readings at configured sampling intervals (10-second default) without operator intervention
- **SC-003**: Operators can identify devices in warning or critical state within 5 seconds of dashboard access through color-coded visual indicators
- **SC-004**: Admins can complete full device configuration (connection, thresholds, settings) in under 5 minutes for a standard Modbus device
- **SC-005**: System successfully connects to and collects data from 95% of standard Modbus TCP/IP devices without custom configuration
- **SC-006**: Historical data queries for 24-hour time range return results in under 2 seconds for typical device
- **SC-007**: CSV export completes within 10 seconds for 1 week of data for a single device
- **SC-008**: System handles 100+ concurrent user sessions without performance degradation
- **SC-009**: Dashboard charts render and update smoothly at 30+ FPS on standard hardware
- **SC-010**: System uptime exceeds 99.5% during normal operation (excluding planned maintenance)
- **SC-011**: Data loss during normal operation is zero; all readings collected per sampling interval are persisted
- **SC-012**: Owner can create new user accounts and assign roles in under 2 minutes
- **SC-013**: System works on tablets with touch-friendly controls requiring no mouse/keyboard
- **SC-014**: System successfully deploys on customer's on-premises server and operates without internet connectivity
- **SC-015**: Operators require less than 30 minutes of training to use core monitoring features effectively
- **SC-016**: 90% of device threshold violations are detected and displayed within 10 seconds of occurrence
- **SC-017**: Zero security vulnerabilities in authentication and authorization mechanisms (verified through security audit)
- **SC-018**: System automatically recovers from database connection failures within 30 seconds
- **SC-019**: Historical data retention and cleanup operates automatically without manual intervention
