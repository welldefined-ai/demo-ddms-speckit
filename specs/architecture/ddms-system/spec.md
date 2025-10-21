# DDMS System Architecture

## Purpose

Describes the overall architecture of the Device Data Monitoring System (DDMS), a web-based industrial IoT platform for monitoring Modbus TCP devices with real-time data collection, historical analytics, and role-based access control.

## System Context

```
┌─────────────────┐
│  Web Browser    │
│  (Frontend UI)  │
└────────┬────────┘
         │ HTTPS/WebSocket
         ↓
┌─────────────────────────────────┐
│     FastAPI Backend             │
│  - REST API                     │
│  - Server-Sent Events (SSE)     │
│  - JWT Authentication           │
│  - Business Logic Services      │
└────────┬────────────────────────┘
         │ SQL/asyncpg
         ↓
┌─────────────────────────────────┐
│   PostgreSQL + TimescaleDB      │
│  - Time-series data storage     │
│  - Device configuration         │
│  - User management              │
└─────────────────────────────────┘
         ↑
         │ Modbus TCP
┌────────┴────────────────────────┐
│   Industrial Devices            │
│  - Sensors                      │
│  - PLCs                         │
│  - SCADA equipment              │
└─────────────────────────────────┘
```

## Components

### Component: Frontend Application

**Type**: Single Page Application (SPA)
**Technology**: React 18.2.0 with TypeScript 5.3.2
**Build Tool**: Vite 5.0.4
**Responsibility**: User interface for device monitoring, configuration, and data visualization

**Directory Structure**:
```
frontend/
├── src/
│   ├── pages/          # Route-level components
│   ├── components/     # Reusable UI components
│   ├── services/       # API client, SSE subscription
│   ├── contexts/       # React context (AuthContext)
│   ├── utils/          # Helper functions
│   ├── locales/        # i18n translations (en, zh)
│   └── styles/         # Global CSS
```

**Key Features**:
- Real-time dashboard with device status cards
- Historical data visualization with ECharts
- Device and group CRUD operations
- User authentication and authorization UI
- Internationalization (English, Chinese)
- CSV data export

**Dependencies**:
- **React Router** (6.20.0): Client-side routing
- **Axios** (1.12.2): HTTP client with interceptors for auth
- **ECharts** (5.6.0): Interactive charting library
- **i18next** (23.7.6): Internationalization framework
- **date-fns** (4.1.0): Date manipulation

**Interfaces**:
- REST API client connects to backend at `VITE_API_BASE_URL`
- SSE client subscribes to `/api/devices/stream` for real-time updates
- Bearer token authentication via Authorization header

**Configuration**:
- `VITE_API_BASE_URL`: Backend API base URL (default: http://localhost:8000)
- `VITE_CHART_UPDATE_INTERVAL`: Chart refresh interval (default: 5000ms)
- `VITE_APP_TITLE`: Application title

**Deployment**: Static files served via Nginx or CDN

---

### Component: Backend API Server

**Type**: RESTful API with real-time streaming
**Technology**: Python 3.11+ with FastAPI 0.104.1
**Web Server**: Uvicorn 0.24.0 (ASGI server)
**Responsibility**: Business logic, authentication, data aggregation, Modbus communication

**Directory Structure**:
```
backend/
├── src/
│   ├── main.py         # FastAPI app initialization
│   ├── api/            # Route handlers
│   │   ├── auth.py
│   │   ├── devices.py
│   │   ├── readings.py
│   │   ├── groups.py
│   │   ├── users.py
│   │   ├── export.py
│   │   ├── schemas.py      # Pydantic models
│   │   ├── dependencies.py # Dependency injection
│   │   └── errors.py       # Exception handlers
│   ├── models/         # SQLAlchemy ORM models
│   ├── services/       # Business logic layer
│   ├── collectors/     # Modbus data collection
│   ├── db/             # Database session, migrations
│   └── utils/          # Auth, RBAC, logging, metrics
```

**Key Features**:
- RESTful API for device, group, user, reading management
- Server-Sent Events (SSE) for real-time device streaming
- JWT-based authentication with refresh tokens
- Role-based access control (Owner, Admin, ReadOnly)
- Modbus TCP client for device communication
- Background data collection orchestration
- CSV export with streaming
- Prometheus metrics endpoint

**Dependencies**:
- **FastAPI** (0.104.1): Web framework
- **SQLAlchemy** (2.0.23): ORM
- **asyncpg** (0.29.0): Async PostgreSQL driver
- **pymodbus** (3.5.4): Modbus TCP client
- **python-jose** (3.3.0): JWT token generation/validation
- **passlib[bcrypt]** (1.7.4): Password hashing
- **pandas** (2.1.3): Data aggregation for exports
- **prometheus-client** (0.19.0): Metrics collection

**Interfaces**:
- REST API endpoints (see API specifications)
- SSE stream: `/api/devices/stream`
- Modbus TCP client connections to industrial devices
- PostgreSQL database via SQLAlchemy

**Configuration** (Environment Variables):
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET_KEY`: Secret for JWT signing
- `JWT_ALGORITHM`: HS256
- `ACCESS_TOKEN_EXPIRE_MINUTES`: 30
- `CORS_ORIGINS`: Allowed frontend origins
- `MODBUS_TIMEOUT`: 10 seconds
- `MODBUS_RETRY_ATTEMPTS`: 3
- `PROMETHEUS_ENABLED`: True

**Scaling**:
- Stateless API servers (horizontal scaling)
- Background tasks via asyncio for data collection
- Connection pooling for database

**Monitoring**:
- Structured logging via Python logging module
- Prometheus metrics: request counts, latencies, device status
- Health check endpoint: `/`

---

### Component: Database (PostgreSQL + TimescaleDB)

**Type**: Relational database with time-series extension
**Technology**: PostgreSQL 15 with TimescaleDB extension
**Responsibility**: Persistent storage for time-series readings, device configuration, user accounts

**Tables**:
1. **users**: User accounts with RBAC roles
2. **devices**: Modbus device configuration
3. **readings**: Time-series sensor data (hypertable)
4. **groups**: Device logical groupings
5. **device_groups**: Many-to-many device-group associations
6. **configuration**: System-wide settings (singleton)

**TimescaleDB Features**:
- Hypertable on `readings` partitioned by `timestamp`
- Continuous aggregates: `readings_1min`, `readings_1hour`, `readings_1day`
- Automatic chunk management and compression
- Retention policies for automatic data cleanup

**Indexes**:
- `ix_users_username`: Username lookup
- `ix_devices_name`: Device name lookup
- `ix_groups_name`: Group name lookup
- `idx_readings_device_timestamp`: Composite index for time-range queries

**Migrations**:
- Alembic 1.12.1 for schema versioning
- Migrations in `backend/src/db/migrations/versions/`
  - `001_initial_schema.py`: Create tables
  - `002_add_continuous_aggregates.py`: TimescaleDB aggregates

**Backup**:
- Configurable backup schedule (cron: "0 2 * * *")
- Backup retention configurable in configuration table

**Deployment**:
- Docker container: `timescale/timescaledb:latest-pg15`
- Volume mount for persistent storage

---

### Component: Modbus Data Collector

**Type**: Background service (embedded in backend)
**Technology**: Python asyncio with pymodbus 3.5.4
**Responsibility**: Periodic polling of Modbus TCP devices and storing readings

**Implementation**:
- `backend/src/collectors/modbus_collector.py`: Modbus TCP client
- `backend/src/collectors/device_manager.py`: Polling orchestration

**Behavior**:
- Runs as async background task started with FastAPI app
- Polls each device according to `sampling_interval` (1-3600 seconds)
- Concurrent polling using asyncio (non-blocking)
- Retry logic: Up to 3 attempts on connection failure
- Timeout: 10 seconds per Modbus request

**Protocol**:
- Modbus TCP/IP (not RTU or ASCII)
- Function code 0x03 (Read Holding Registers)
- Configurable slave ID (1-247)
- Configurable register address and count

**Status Updates**:
- Updates device.status: ONLINE, OFFLINE, ERROR
- Updates device.last_reading_at on success
- Stores reading in readings table

**Error Handling**:
- Connection timeout → OFFLINE status
- Modbus exception → ERROR status
- Logs all errors to application log

**Scaling**: Embedded in backend process (not separate service)

---

## Design Decisions

### Decision: TimescaleDB for Time-Series Data

**Status**: Accepted
**Date**: Initial implementation (from git history analysis)

**Context**:
System requires efficient storage and querying of high-frequency time-series readings (potentially millions of data points per day across many devices). Standard PostgreSQL tables would become inefficient for time-range queries on large datasets.

**Decision**:
Use TimescaleDB extension on PostgreSQL to convert `readings` table to hypertable with automatic time-based partitioning.

**Consequences**:
- ✅ Efficient time-range queries via chunk pruning
- ✅ Automatic data retention policies
- ✅ Pre-computed aggregates (1min, 1hour, 1day) for fast dashboard loading
- ✅ Maintains PostgreSQL compatibility (standard SQL, joins, constraints)
- ✅ Horizontal scaling via distributed hypertables (future capability)
- ⚠️ Additional dependency (TimescaleDB extension)
- ⚠️ Learning curve for hypertable-specific features

**Alternatives Considered**:
- InfluxDB: Specialized time-series DB but requires separate database system
- MongoDB: Document-based, less efficient for time-range aggregations
- Raw PostgreSQL: Simpler but poor performance at scale

---

### Decision: Server-Sent Events (SSE) for Real-Time Updates

**Status**: Accepted
**Date**: Initial implementation

**Context**:
Dashboard requires real-time updates of device readings without constant polling. Need to push updates from server to multiple connected clients efficiently.

**Decision**:
Implement Server-Sent Events (SSE) endpoint at `/api/devices/stream` that broadcasts device readings every 5 seconds.

**Consequences**:
- ✅ Simple protocol (HTTP-based, no WebSocket complexity)
- ✅ Automatic reconnection in browsers
- ✅ Unidirectional (server → client) sufficient for use case
- ✅ Works through standard HTTP/2 infrastructure
- ✅ No authentication required (public endpoint for monitoring displays)
- ⚠️ Higher server memory for long-lived connections
- ⚠️ No client → server messaging (acceptable for current requirements)

**Alternatives Considered**:
- WebSocket: More complex, bidirectional (not needed)
- Long polling: Less efficient, more HTTP overhead
- GraphQL subscriptions: Requires GraphQL adoption

---

### Decision: JWT with Refresh Tokens

**Status**: Accepted
**Date**: Initial implementation

**Context**:
Need stateless authentication for API that supports web and potential mobile clients. Must balance security (short token lifetime) with user experience (not forcing frequent re-login).

**Decision**:
Use JWT access tokens (30 minute expiry) with refresh tokens (7 day expiry stored in httpOnly cookies).

**Consequences**:
- ✅ Stateless authentication (no server-side session storage)
- ✅ Horizontal scaling without session affinity
- ✅ Short-lived access tokens limit exposure if compromised
- ✅ Refresh tokens in httpOnly cookies prevent XSS theft
- ✅ Industry-standard approach
- ⚠️ Token revocation requires blacklist or database lookup (not currently implemented)
- ⚠️ Refresh token rotation adds complexity

**Alternatives Considered**:
- Session-based auth: Requires session store (Redis), more complex scaling
- OAuth2/OIDC: Overkill for single-tenant system
- API keys: Less secure, no expiration

---

### Decision: Three-Tier RBAC (Owner/Admin/ReadOnly)

**Status**: Accepted
**Date**: Initial implementation

**Context**:
System deployed in industrial environments with different user roles: operators (view-only), engineers (device configuration), administrators (user management). Need to enforce principle of least privilege.

**Decision**:
Implement three-tier role hierarchy:
- **Owner**: Full system access including user management
- **Admin**: Device/group management, no user management
- **ReadOnly**: View-only access to dashboards and data

**Consequences**:
- ✅ Clear separation of concerns
- ✅ Simple to understand and communicate
- ✅ Enforced at API level via @require_roles decorator
- ✅ Supports common organizational structures
- ⚠️ May require more granular permissions in future (e.g., per-device access)
- ⚠️ Currently no group-level permissions

**Alternatives Considered**:
- Two-tier (admin/user): Too coarse-grained
- Fine-grained permissions (ACLs): Too complex for initial requirements
- Attribute-based access control (ABAC): Overkill for current scale

---

### Decision: FastAPI for Backend Framework

**Status**: Accepted
**Date**: Initial implementation

**Context**:
Need modern Python web framework that supports async I/O for Modbus client, automatic API documentation, and strong typing.

**Decision**:
Use FastAPI with Pydantic for request/response validation.

**Consequences**:
- ✅ Native async/await support for Modbus collector
- ✅ Automatic OpenAPI/Swagger documentation
- ✅ Pydantic validation reduces boilerplate
- ✅ High performance (comparable to Node.js, Go)
- ✅ Type hints improve code quality
- ✅ Modern Python features (3.11+)
- ⚠️ Relatively newer framework (less mature ecosystem than Flask/Django)

**Alternatives Considered**:
- Flask: Synchronous, requires Celery for background tasks
- Django: Too heavyweight for API-only service
- Express.js: Would require Node.js for Modbus libraries

---

### Decision: React with TypeScript for Frontend

**Status**: Accepted
**Date**: Initial implementation

**Context**:
Need responsive web UI for device monitoring with real-time updates, interactive charts, and internationalization.

**Decision**:
Build SPA with React 18 + TypeScript, using Vite as build tool.

**Consequences**:
- ✅ Component reusability
- ✅ Strong typing with TypeScript prevents runtime errors
- ✅ Vite provides fast development experience
- ✅ Large ecosystem for charts (ECharts), i18n, routing
- ✅ Easy SSE integration
- ⚠️ Bundle size management required
- ⚠️ SEO limitations (mitigated by being internal tool)

**Alternatives Considered**:
- Vue.js: Smaller ecosystem for industrial dashboards
- Angular: Too heavyweight, steeper learning curve
- Svelte: Less mature ecosystem

---

## Performance Characteristics

| Metric | Current | Measurement |
|--------|---------|-------------|
| Device Polling Interval | 1-3600 seconds | Configurable per device |
| SSE Update Frequency | 5 seconds | Hardcoded in devices.py:stream endpoint |
| Concurrent Device Connections | 100+ | Tested with asyncio, limited by network |
| API Response Time (p95) | < 200ms | Typical for device list, reading queries |
| Time-Range Query (1 day) | < 500ms | With TimescaleDB on 1M+ readings |
| Aggregated Query (1 month, 1-hour buckets) | < 1s | Using continuous aggregates |
| Database Connection Pool | 10-20 connections | SQLAlchemy pool_size |
| Token Validation Overhead | < 5ms | JWT decode + signature verification |

## Deployment Architecture

**Development**:
```
Docker Compose:
  - frontend: Vite dev server on :3000
  - backend: Uvicorn with reload on :8000
  - database: TimescaleDB on :5432
```

**Production** (example):
```
┌────────────────┐
│  Nginx/Caddy   │  → TLS termination, static files
└───────┬────────┘
        │
    ┌───┴────┐
    │ Load   │
    │Balancer│
    └───┬────┘
        │
   ┌────┴─────────┐
   │  Backend     │  → Multiple Uvicorn workers
   │  Instances   │
   │  (horizontal)│
   └────┬─────────┘
        │
   ┌────┴─────────┐
   │ PostgreSQL   │  → TimescaleDB with replication
   │ + TimescaleDB│
   └──────────────┘
```

**Container Strategy**:
- Frontend: Multi-stage build (node build → nginx serve)
- Backend: Python 3.11 with pip dependencies
- Database: Official timescaledb/timescaledb image

**Environment Management**:
- `.env` files for configuration
- Separate configs for dev/staging/prod
- Secrets managed via environment variables (not in repo)

## Security Considerations

**Authentication**:
- Bcrypt password hashing (cost factor 12)
- JWT tokens with HS256 signing
- Refresh tokens in httpOnly, secure, SameSite=Strict cookies
- No password storage in plaintext or logs

**Authorization**:
- Role-based access control enforced at API layer
- Decorator-based authorization checks
- 403 Forbidden for insufficient permissions

**CORS**:
- Configurable allowed origins (CORS_ORIGINS)
- Development: localhost
- Production: Specific domain whitelist

**Input Validation**:
- Pydantic schemas validate all API inputs
- SQL injection prevented by SQLAlchemy parameterized queries
- Modbus protocol errors caught and logged

**Network Security**:
- Modbus TCP connections timeout after 10 seconds
- No exposed Modbus ports to internet (internal network only)
- HTTPS enforced in production (TLS 1.2+)

**Secrets**:
- JWT_SECRET_KEY must be strong random string
- Database credentials in environment variables
- No secrets in git repository

## Related Specs

- **Capabilities**: All capability specs
- **Data Models**: All data model schemas
- **APIs**: All API specifications
