# Export API

## Purpose

The Export API provides data export capabilities for device readings in CSV format. It enables users to download historical data for analysis, reporting, and archival purposes. The API supports exporting data from individual devices, device groups, or multiple selected devices with optional time range filtering and data aggregation.

## Base Configuration

**Base URL**: `/api/export`
**Authentication**: Required for all endpoints (Bearer token)

## Endpoints

### GET /api/export/device/{device_id}

Export device readings to CSV format.

**Authentication**: Required

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `device_id` | UUID | Device UUID |

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_time` | string | No | Start timestamp (ISO 8601 format, inclusive) |
| `end_time` | string | No | End timestamp (ISO 8601 format, inclusive) |
| `aggregate` | string | No | Aggregation interval: `1min`, `1hour`, or `1day` |

**Time Range Filtering**:
- If neither `start_time` nor `end_time` is provided, exports all available data
- If only `start_time` is provided, exports from that time forward
- If only `end_time` is provided, exports up to that time
- If both provided, exports within the time range (inclusive)

**Aggregation**:
- When `aggregate` is specified, data is grouped by time buckets
- Returns statistical aggregates instead of raw readings
- Supported intervals: `1min`, `1hour`, `1day`

**Responses**:

#### 200 OK (Raw Data)

When no aggregation is specified, returns CSV with raw readings.

**Content-Type**: `text/csv`

**Headers**:
- `Content-Disposition: attachment; filename=<device_name>_<timestamp>.csv`
- `Cache-Control: no-cache`

**CSV Format** (Raw Data):

```csv
timestamp,value,unit
2025-10-20T10:30:00Z,25.5,°C
2025-10-20T10:29:50Z,25.4,°C
2025-10-20T10:29:40Z,25.3,°C
```

**CSV Columns** (Raw Data):

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | string | Reading timestamp (ISO 8601) |
| `value` | float | Measured value |
| `unit` | string | Measurement unit |

#### 200 OK (Aggregated Data)

When `aggregate` parameter is provided, returns CSV with aggregated statistics.

**CSV Format** (Aggregated Data):

```csv
time_bucket,avg_value,min_value,max_value,count,unit
2025-10-20T10:00:00Z,25.3,24.8,25.9,120,°C
2025-10-20T09:00:00Z,24.8,24.2,25.4,120,°C
```

**CSV Columns** (Aggregated Data):

| Column | Type | Description |
|--------|------|-------------|
| `time_bucket` | string | Start of time bucket (ISO 8601) |
| `avg_value` | float | Average value in the bucket |
| `min_value` | float | Minimum value in the bucket |
| `max_value` | float | Maximum value in the bucket |
| `count` | integer | Number of readings in the bucket |
| `unit` | string | Measurement unit |

**Filename Format**: `<device_name>_<YYYYMMDD_HHMMSS>.csv`

Example: `Temperature_Sensor_1_20251020_103000.csv`

#### 400 Bad Request

Invalid time range or parameters.

```json
{
  "detail": "Invalid timestamp format: Invalid isoformat string"
}
```

#### 401 Unauthorized

Not authenticated.

```json
{
  "detail": "Invalid or expired token"
}
```

#### 404 Not Found

Device not found.

```json
{
  "detail": "Device 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

---

### GET /api/export/group/{group_id}

Export readings from all devices in a group to CSV format.

**Authentication**: Required

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `group_id` | UUID | Group UUID |

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_time` | string | No | Start timestamp (ISO 8601 format, inclusive) |
| `end_time` | string | No | End timestamp (ISO 8601 format, inclusive) |

**Note**: Group exports do not support aggregation. All readings from all devices in the group are exported in raw format.

**Responses**:

#### 200 OK

Returns CSV with readings from all devices in the group.

**Content-Type**: `text/csv`

**Headers**:
- `Content-Disposition: attachment; filename=<group_name>_<timestamp>.csv`
- `Cache-Control: no-cache`

**CSV Format**:

```csv
timestamp,device_name,value,unit
2025-10-20T10:30:00Z,Temperature Sensor 1,25.5,°C
2025-10-20T10:30:05Z,Temperature Sensor 2,26.2,°C
2025-10-20T10:29:55Z,Temperature Sensor 1,25.4,°C
```

**CSV Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | string | Reading timestamp (ISO 8601) |
| `device_name` | string | Name of the device |
| `value` | float | Measured value |
| `unit` | string | Measurement unit |

**Filename Format**: `<group_name>_<YYYYMMDD_HHMMSS>.csv`

Example: `Building_A_Sensors_20251020_103000.csv`

#### 400 Bad Request

Invalid time range or parameters.

```json
{
  "detail": "Invalid timestamp format: Invalid isoformat string"
}
```

#### 401 Unauthorized

Not authenticated.

```json
{
  "detail": "Invalid or expired token"
}
```

#### 404 Not Found

Group not found.

```json
{
  "detail": "Group 323e4567-e89b-12d3-a456-426614174002 not found"
}
```

---

### GET /api/export/devices

Export readings from multiple selected devices to a single CSV file.

**Authentication**: Required

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `device_ids` | string | Yes | Comma-separated list of device UUIDs |
| `start_time` | string | No | Start timestamp (ISO 8601 format, inclusive) |
| `end_time` | string | No | End timestamp (ISO 8601 format, inclusive) |

**Example Query**: `/api/export/devices?device_ids=123e4567-e89b-12d3-a456-426614174000,223e4567-e89b-12d3-a456-426614174001&start_time=2025-10-20T00:00:00Z`

**Responses**:

#### 200 OK

Returns CSV with readings from all specified devices.

**Content-Type**: `text/csv`

**Headers**:
- `Content-Disposition: attachment; filename=multi_device_export_<timestamp>.csv`
- `Cache-Control: no-cache`

**CSV Format**:

```csv
timestamp,device_name,value,unit
2025-10-20T10:30:00Z,Temperature Sensor 1,25.5,°C
2025-10-20T10:30:05Z,Temperature Sensor 2,26.2,°C
2025-10-20T10:29:55Z,Temperature Sensor 1,25.4,°C
```

**CSV Columns**: Same as group export (timestamp, device_name, value, unit)

**Filename Format**: `multi_device_export_<YYYYMMDD_HHMMSS>.csv`

Example: `multi_device_export_20251020_103000.csv`

#### 400 Bad Request

Invalid parameters or no devices specified.

```json
{
  "detail": "Invalid device ID format: badly formed hexadecimal UUID string"
}
```

Or:

```json
{
  "detail": "At least one device ID must be specified"
}
```

#### 401 Unauthorized

Not authenticated.

```json
{
  "detail": "Invalid or expired token"
}
```

#### 404 Not Found

No devices found or no data available.

```json
{
  "detail": "No devices found or no data available for the specified devices"
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| EXPORT_001 | 400 | Invalid timestamp format |
| EXPORT_002 | 400 | Invalid time range (end before start) |
| EXPORT_003 | 400 | Invalid device ID format |
| EXPORT_004 | 400 | No device IDs specified |
| EXPORT_005 | 400 | Invalid aggregation interval |
| EXPORT_006 | 401 | Not authenticated |
| EXPORT_007 | 404 | Device not found |
| EXPORT_008 | 404 | Group not found |
| EXPORT_009 | 404 | No devices found or no data available |

## CSV Format Details

### Character Encoding
- UTF-8 encoding is used for all CSV files
- Supports international characters in device names and units

### Field Formatting
- Timestamps are in ISO 8601 format with UTC timezone (Z suffix)
- Numeric values use standard decimal notation (e.g., 25.5)
- String fields are not quoted unless they contain special characters (comma, newline)

### Empty Results
- If no data is available for the specified time range, an empty CSV with headers is returned

### Data Ordering
- Raw data: Ordered by timestamp descending (most recent first)
- Aggregated data: Ordered by time bucket descending
- Multi-device exports: Ordered by timestamp descending across all devices

## Performance Considerations

1. **Large Exports**: For very large time ranges, consider using aggregation to reduce file size
2. **Multiple Devices**: The multi-device export endpoint is limited to 1000 readings by default
3. **Streaming**: Export responses are generated on-demand (not streamed), so very large exports may take time
4. **Concurrent Exports**: Multiple users can export simultaneously without affecting each other

## Use Cases

1. **Archival**: Export all historical data for long-term storage
2. **Analysis**: Export data for analysis in spreadsheet or data analysis tools
3. **Reporting**: Generate periodic reports by exporting data for specific time ranges
4. **Compliance**: Export data for regulatory compliance and audit trails
5. **Troubleshooting**: Export detailed readings for investigating device behavior
6. **Comparative Analysis**: Export multiple devices to compare performance

## Related Specs

- **Capabilities**: Data export (CAP-010), CSV generation (CAP-011)
- **Data Models**: Reading model, Device model, Group model
- **Services**: export_service for CSV generation
- **APIs**: Reading API (for querying data), Group API (for group membership)
