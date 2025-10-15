# User Requirements

DDMS (Device Data Monitoring System) is a web-based application for monitoring and analyzing industrial device data in factory or coalmine environments.

## Deployment

**[DDMS-DEP-010]** The system _shall_ be deployed on the customer's intranet (on-premises server).

**[DDMS-DEP-020]** The system _shall_ be accessible via web browser from the internal network without requiring external internet connection.

**[DDMS-DEP-030]** The system _shall_ support modern web browsers including Chrome, Firefox, Edge, and Safari.

**[DDMS-DEP-040]** The system _shall_ provide responsive design for desktop and tablet access.

## Authentication & Authorization

**[DDMS-AUTH-010]** The system _shall_ provide a default owner account with username and password on initial setup.

**[DDMS-AUTH-020]** The owner _shall_ be able to change their own username and password.

**[DDMS-AUTH-030]** The owner _shall_ be able to create new admin user accounts.

**[DDMS-AUTH-040]** The owner _shall_ be able to create new read-only user accounts.

**[DDMS-AUTH-050]** The owner _shall_ be able to delete user accounts except the owner account.

**[DDMS-AUTH-060]** The owner role _shall_ have full system access and user management privileges.

**[DDMS-AUTH-070]** The admin role _shall_ have full access to device configuration and monitoring.

**[DDMS-AUTH-080]** The read-only role _shall_ have view-only access to dashboards and data.

## Real-time Monitoring

**[DDMS-MON-010]** The system _shall_ display current readings from all connected monitoring devices.

**[DDMS-MON-020]** The system _shall_ show device data in chart format (line charts, gauges, etc.).

**[DDMS-MON-030]** The system _shall_ auto-refresh data at configured sampling intervals.

**[DDMS-MON-040]** The system _shall_ support displaying multiple devices simultaneously.

**[DDMS-MON-050]** _When_ a reading approaches a threshold, the system _shall_ display a yellow warning indicator.

**[DDMS-MON-060]** _When_ a reading exceeds or falls below a critical threshold, the system _shall_ display a red warning indicator.

**[DDMS-MON-070]** The system _shall_ display visual warning indicators on both charts and device lists.

**[DDMS-MON-080]** The system _shall_ overlay threshold lines on trend charts.

**[DDMS-MON-090]** The system _shall_ display current reading value and threshold values on charts.

**[DDMS-MON-100]** The system _shall_ show color-coded regions (normal/warning/critical) on charts.

**[DDMS-MON-110]** The system _shall_ provide hover tooltips showing exact values and timestamps.

## Historical Data

**[DDMS-HIST-010]** The system _shall_ allow users to view historical trend curves for any device reading.

**[DDMS-HIST-020]** The system _shall_ allow users to customize the time range for historical data (e.g., last hour, last 24 hours, last week, custom range).

**[DDMS-HIST-030]** The system _shall_ allow users to zoom in/out on specific time periods in historical charts.

**[DDMS-HIST-040]** The system _shall_ allow users to export historical data to CSV files.

**[DDMS-HIST-050]** The system _shall_ display threshold lines on historical trend charts.

## Device Configuration

**[DDMS-DEV-010]** Admin and owner users _shall_ be able to add new monitoring devices.

**[DDMS-DEV-020]** _When_ adding a device, the system _shall_ allow configuration of connection parameters (Modbus settings).

**[DDMS-DEV-030]** _When_ configuring a device, the system _shall_ allow setting device name and description.

**[DDMS-DEV-040]** _When_ configuring a device, the system _shall_ allow setting reading units (e.g., °C, bar, RPM, %).

**[DDMS-DEV-050]** _When_ configuring a device, the system _shall_ allow setting sampling interval.

**[DDMS-DEV-060]** _When_ configuring a device, the system _shall_ allow setting data retention period.

**[DDMS-DEV-070]** _When_ configuring a device, the system _shall_ allow setting upper threshold limits (warning and critical).

**[DDMS-DEV-080]** _When_ configuring a device, the system _shall_ allow setting lower threshold limits (warning and critical).

**[DDMS-DEV-090]** _When_ configuring a device, the system _shall_ allow setting hysteresis values to prevent alarm flapping.

**[DDMS-DEV-100]** Admin and owner users _shall_ be able to delete devices.

**[DDMS-DEV-110]** _When_ deleting a device, the system _shall_ provide an option to keep or delete historical data.

**[DDMS-DEV-120]** The system _shall_ display device connection status (online/offline).

**[DDMS-DEV-130]** The system _shall_ display last successful reading timestamp for each device.

**[DDMS-DEV-140]** The system _shall_ display communication error indicators for devices.

## Device Grouping

**[DDMS-GRP-010]** Admin and owner users _shall_ be able to create logical groups of devices.

**[DDMS-GRP-020]** The system _shall_ allow assigning devices to one or more groups.

**[DDMS-GRP-030]** Admin and owner users _shall_ be able to rename groups.

**[DDMS-GRP-040]** Admin and owner users _shall_ be able to delete groups.

**[DDMS-GRP-050]** _When_ viewing a group, the system _shall_ provide a real-time monitoring dashboard showing all devices in the group.

**[DDMS-GRP-060]** _When_ viewing a group, the system _shall_ provide historical trend charts for the group.

**[DDMS-GRP-070]** _When_ viewing a group, the system _shall_ display a group-level alert summary.

**[DDMS-GRP-080]** _When_ viewing a group, the system _shall_ allow CSV export for all group devices.

## Internationalization

**[DDMS-I18N-010]** The system _shall_ support English (en-US) language.

**[DDMS-I18N-020]** The system _shall_ support Chinese (zh-CN) language.

**[DDMS-I18N-030]** Users _shall_ be able to switch language from the UI.

**[DDMS-I18N-040]** The system _shall_ save language preference per user account.

**[DDMS-I18N-050]** All UI elements, labels, and messages _shall_ be translated for supported languages.

## User Interface

**[DDMS-UI-010]** The system _shall_ provide a clean, modern interface design.

**[DDMS-UI-020]** The system _shall_ provide intuitive navigation and workflows.

**[DDMS-UI-030]** The system _shall_ have a professional appearance suitable for industrial environments.

**[DDMS-UI-040]** The system _shall_ provide smooth transitions between views.

**[DDMS-UI-050]** The system _shall_ provide animated chart updates.

**[DDMS-UI-060]** The system _shall_ display loading indicators for asynchronous operations.

**[DDMS-UI-070]** The system _shall_ provide responsive feedback for user actions.

**[DDMS-UI-080]** The system _shall_ provide subtle hover and focus effects.

**[DDMS-UI-090]** The system _shall_ ensure high contrast between text and backgrounds.

**[DDMS-UI-100]** The system _shall_ provide clear visual hierarchy.

**[DDMS-UI-110]** The system _shall_ use readable fonts at typical viewing distances.

**[DDMS-UI-120]** The system _shall_ provide touch-friendly controls for tablet access.

## Data Persistence

**[DDMS-DATA-010]** The system _shall_ store all configuration data persistently on the server.

**[DDMS-DATA-020]** The system _shall_ store time-series data in a database.

**[DDMS-DATA-030]** The system _shall_ provide automatic database backups on a configurable schedule.

**[DDMS-DATA-040]** The system _shall_ enforce configurable retention period per device.

**[DDMS-DATA-050]** The system _shall_ automatically clean up old data based on retention period.

**[DDMS-DATA-060]** The system _shall_ allow manual data export before deletion.

**[DDMS-DATA-070]** Data _shall_ persist across server restarts.

**[DDMS-DATA-080]** The system _shall_ ensure transaction safety for configuration changes.

**[DDMS-DATA-090]** The system _shall_ provide error recovery mechanisms.

## Protocol Support

**[DDMS-PROTO-010]** The system _shall_ support Modbus TCP/IP protocol.

**[DDMS-PROTO-020]** The system _shall_ support Modbus RTU over serial (optional).

**[DDMS-PROTO-030]** The system _shall_ allow configurable register addresses for Modbus devices.

**[DDMS-PROTO-040]** The system _shall_ allow configurable data types for Modbus devices.

**[DDMS-PROTO-050]** The system _shall_ support common industrial PLCs and sensors.
