# Reading API

## Purpose

The Reading API provides access to historical device reading data with support for time range filtering, pagination, and data aggregation. It enables querying device measurements over time with flexible granularity for analysis and reporting.

## Base Configuration

**Base URL**: `/api/readings`
**Authentication**: Required for all endpoints (Bearer token)

## Endpoints

### GET /api/readings/{device_id}

Get historical readings for a device with optional filtering and aggregation.

**Authentication**: Required

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `device_id` | UUID | Device UUID |

**Query Parameters**:

| Parameter | Type | Required | Default | Constraints | Description |
|-----------|------|----------|---------|-------------|-------------|
| `start_time` | string | No | None | ISO 8601 | Start timestamp (inclusive) |
| `end_time` | string | No | None | ISO 8601 | End timestamp (inclusive) |
| `limit` | integer | No | 100 | 1-1000 | Maximum number of readings to return |
| `offset` | integer | No | 0 | >= 0 | Number of readings to skip (pagination) |
| `aggregate` | string | No | None | 1min, 1hour, 1day | Aggregation interval |

**Time Range Filtering**:
- If neither `start_time` nor `end_time` is provided, returns most recent readings
- If only `start_time` is provided, returns readings from that time forward
- If only `end_time` is provided, returns readings up to that time
- If both provided, returns readings within the time range (inclusive)
- Time format: ISO 8601 (e.g., "2025-10-20T10:30:00Z" or "2025-10-20T10:30:00+00:00")

**Pagination**:
- Use `limit` and `offset` for pagination through large result sets
- `total` field in response indicates total number of readings available

**Aggregation**:
- When `aggregate` is specified, readings are grouped by time buckets
- Supported intervals: `1min`, `1hour`, `1day`
- Returns statistical aggregates (avg, min, max, count) instead of raw readings
- Pagination still applies to aggregated results

**Responses**:

#### 200 OK (Raw Readings)

When no aggregation is specified, returns raw readings:

```json
{
  "device_id": "123e4567-e89b-12d3-a456-426614174000",
  "readings": [
    {
      "timestamp": "2025-10-20T10:30:00Z",
      "value": 25.5
    },
    {
      "timestamp": "2025-10-20T10:29:50Z",
      "value": 25.4
    }
  ],
  "total": 150
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `device_id` | string | Device UUID |
| `readings` | array | Array of reading objects |
| `readings[].timestamp` | string | Reading timestamp (ISO 8601) |
| `readings[].value` | float | Measured value |
| `total` | integer | Total number of readings matching the query |

#### 200 OK (Aggregated Readings)

When `aggregate` parameter is provided, returns aggregated data:

```json
{
  "device_id": "123e4567-e89b-12d3-a456-426614174000",
  "readings": [
    {
      "timestamp": "2025-10-20T10:00:00Z",
      "value": 25.3
    },
    {
      "timestamp": "2025-10-20T09:00:00Z",
      "value": 24.8
    }
  ],
  "total": 24
}
```

**Note**: In the current implementation, aggregated readings return the average value in the `value` field for consistency with the response schema. The full aggregation data (min, max, count) is computed by the service layer but simplified in the API response.

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

### GET /api/readings/{device_id}/latest

Get the most recent reading for a device.

**Authentication**: Required

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `device_id` | UUID | Device UUID |

**Responses**:

#### 200 OK

Returns the latest reading.

```json
{
  "device_id": "123e4567-e89b-12d3-a456-426614174000",
  "timestamp": "2025-10-20T10:30:00Z",
  "value": 25.5
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `device_id` | string | Device UUID |
| `timestamp` | string | Reading timestamp (ISO 8601) |
| `value` | float | Measured value |

#### 401 Unauthorized

Not authenticated.

```json
{
  "detail": "Invalid or expired token"
}
```

#### 404 Not Found

Device not found or has no readings.

```json
{
  "detail": "Device not found or has no readings"
}
```

---

### GET /api/readings/{device_id}/count

Get the count of readings for a device in a time range.

**Authentication**: Required

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `device_id` | UUID | Device UUID |

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_time` | string | No | Start timestamp (ISO 8601, inclusive) |
| `end_time` | string | No | End timestamp (ISO 8601, inclusive) |

**Responses**:

#### 200 OK

Returns the count of readings.

```json
{
  "device_id": "123e4567-e89b-12d3-a456-426614174000",
  "count": 1500
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `device_id` | string | Device UUID |
| `count` | integer | Number of readings in the specified time range |

#### 400 Bad Request

Invalid time range.

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

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| READING_001 | 400 | Invalid timestamp format |
| READING_002 | 400 | Invalid time range (end before start) |
| READING_003 | 400 | Invalid limit or offset value |
| READING_004 | 400 | Invalid aggregation interval |
| READING_005 | 401 | Not authenticated |
| READING_006 | 404 | Device not found |
| READING_007 | 404 | Device has no readings |

## Performance Considerations

1. **Pagination**: For large result sets, use pagination with appropriate `limit` and `offset` values
2. **Aggregation**: Use aggregation for long time ranges to reduce data volume and improve performance
3. **Time Ranges**: Specify time ranges to limit query scope and improve response times
4. **Indexing**: Queries are optimized with database indexes on device_id and timestamp columns

## Aggregation Details

When using the `aggregate` parameter:

1. **Time Buckets**: Readings are grouped into time buckets based on the specified interval
   - `1min`: 1-minute buckets
   - `1hour`: 1-hour buckets
   - `1day`: 1-day buckets

2. **Statistics Computed**: For each bucket, the service layer computes:
   - `avg_value`: Average of all readings in the bucket
   - `min_value`: Minimum reading in the bucket
   - `max_value`: Maximum reading in the bucket
   - `count`: Number of readings in the bucket

3. **API Response**: Currently simplified to return only the average value for consistency with the response schema

4. **Use Cases**:
   - Trend analysis over long time periods
   - Reducing data volume for visualization
   - Statistical analysis of device behavior

## Related Specs

- **Capabilities**: Historical data access (CAP-004), Data aggregation (CAP-005)
- **Data Models**: Reading model with device relationship
- **Services**: reading_service for data retrieval and aggregation
