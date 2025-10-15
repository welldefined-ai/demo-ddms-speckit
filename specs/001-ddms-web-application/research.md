# Phase 0: Research & Technology Selection

**Feature**: DDMS Web Application  
**Branch**: 001-ddms-web-application  
**Date**: 2025-10-10

## Overview

This document resolves all "NEEDS CLARIFICATION" items from the Technical Context. Each decision includes rationale, alternatives considered, and alignment with constitution requirements.

---

## 1. Python Modbus Library Selection

### Decision: pymodbus 3.x

**Rationale**:
- Most actively maintained Python Modbus library (last update 2024)
- Supports both Modbus TCP/IP (required) and RTU (future FR-065)
- Async/await support via asyncio (constitution requirement for I/O efficiency)
- Comprehensive protocol support (INT16, UINT16, INT32, FLOAT32 per FR-067)
- Well-documented with industrial deployment track record
- MIT license (permissive for on-premises deployment)

**Alternatives Considered**:
- **minimalmodbus**: Serial-only, no TCP/IP support - rejected
- **pyModbusTCP**: TCP-only, no async support - rejected
- **modbus-tk**: Unmaintained since 2019 - rejected

**Implementation Notes**:
- Use `pymodbus.client.tcp.AsyncModbusTcpClient` for async connections
- Implement connection pooling per device to reuse connections
- Configure timeout at 3 seconds (shorter than 10s sampling interval)
- Handle reconnection via 60-second retry policy (per clarification)

**Constitution Alignment**: Async I/O requirement (Principle V), industrial reliability needs (Principle I)

---

## 2. Frontend Framework Selection

### Decision: React 18+ with TypeScript

**Rationale**:
- Largest ecosystem for data visualization libraries
- Strong TypeScript support for type safety (aligns with constitution code quality standards)
- Excellent performance with Virtual DOM and React 18 concurrent features
- Rich charting library options (Chart.js, Recharts, Plotly.js all have React bindings)
- Mature i18n libraries (react-i18next) for EN/CN support (FR-042-046)
- Large talent pool for future maintenance
- Component-based architecture fits modular UI requirements

**Alternatives Considered**:
- **Vue 3**: Simpler learning curve but smaller ecosystem for industrial dashboards - rejected
- **Svelte**: Better performance but less mature ecosystem for real-time charts - rejected
- **Angular**: Too heavy for on-premises deployment, steeper learning curve - rejected

**Implementation Notes**:
- Use Vite for fast development and optimized production builds
- TypeScript strict mode enabled
- ESLint + Prettier for code quality (aligns with constitution formatting requirements)
- React Testing Library + Vitest for component testing

**Constitution Alignment**: Code quality tools (Principle III), efficient visualization (Principle II)

---

## 3. Real-Time Charting Library Selection

### Decision: Apache ECharts (with echarts-for-react wrapper)

**Rationale**:
- Excellent performance with large datasets (handles 8,640 points/device efficiently)
- Built-in time-series optimizations and data sampling for smooth rendering
- Supports real-time updates without full re-renders
- Rich chart types: line charts, gauges, heatmaps for group dashboards
- Strong i18n support (EN/CN built-in) - critical for FR-042-046
- Maintained by Apache Foundation (long-term stability)
- Used in industrial monitoring dashboards (proven track record)
- Free and open-source (Apache 2.0 license)

**Alternatives Considered**:
- **Chart.js**: Simpler but poorer performance with large datasets - rejected
- **Plotly.js**: Rich features but heavier bundle size (1.5MB+ gzipped) - rejected
- **Recharts**: React-native but performance issues with >1000 points - rejected
- **D3.js**: Maximum flexibility but requires more custom code - rejected

**Implementation Notes**:
- Use `dataZoom` component for historical time range selection
- Implement `visualMap` for threshold-based color coding (normal/warning/critical)
- Use `markLine` for threshold overlay lines
- Enable `progressive` rendering for large datasets (> 1000 points)
- Implement data downsampling for export to maintain CSV performance

**Constitution Alignment**: Efficient visualization (Principle II), performance targets (Principle V: 30+ FPS per SC-009)

---

## 4. Time-Series Database Strategy

### Decision: PostgreSQL 15+ with TimescaleDB 2.x Extension

**Rationale**:
- TimescaleDB provides automatic time-series partitioning (hypertables) without schema changes
- Continuous aggregates for fast dashboard queries (pre-computed hourly/daily rollups)
- Native PostgreSQL compatibility - use standard SQLAlchemy ORM
- Data retention policies built-in (automatic deletion per 90-day default)
- Compression reduces storage by 90-95% for historical data
- Mature backup/restore tools (pg_dump, pg_restore)
- Proven scalability (handles millions of readings per day)
- Open-source (Apache 2.0 license) with on-premises deployment

**Alternatives Considered**:
- **InfluxDB**: Specialized TSDB but requires separate query language (InfluxQL/Flux), adds complexity - rejected
- **Native PostgreSQL**: Works but lacks automatic partitioning and compression - rejected
- **Prometheus**: Metrics-focused, not designed for long-term raw data storage - rejected
- **Cassandra**: Over-engineered for 1000-device scale, operational complexity - rejected

**Implementation Notes**:
- Create hypertable on `readings` table partitioned by `timestamp`
- Configure continuous aggregates for 1-minute, 1-hour, 1-day rollups
- Enable compression for data older than 7 days (recent data kept uncompressed for fast inserts)
- Use `SELECT ... WHERE device_id = ? AND timestamp > ? AND timestamp < ?` queries (index-optimized)
- SQLAlchemy will treat TimescaleDB as standard PostgreSQL (no ORM changes needed)

**Constitution Alignment**: Performance targets (Principle V), data reliability (Principle I), efficient storage

---

## 5. Frontend Testing Framework

### Decision: Vitest + React Testing Library + Playwright

**Rationale**:
- **Vitest**: Vite-native test runner, fast execution, excellent TypeScript support
- **React Testing Library**: User-centric testing (tests interaction, not implementation)
- **Playwright**: Cross-browser E2E tests (Chrome, Firefox, Safari per FR-071)
- Combined coverage reporting with c8 (Vitest coverage tool)
- Fast unit tests (<1s per file per constitution requirement)

**Alternatives Considered**:
- **Jest**: Slower with Vite, requires additional configuration - rejected
- **Cypress**: E2E-focused, slower test execution than Playwright - rejected

**Implementation Notes**:
- Unit tests: components, hooks, utilities (aim for 80%+ coverage)
- Integration tests: API client, WebSocket handlers
- E2E tests: critical user journeys (User Stories 1-3 at minimum)
- Coverage threshold configured in vite.config.ts

**Constitution Alignment**: Test-first development (Principle III), >=80% coverage requirement

---

## 6. Authentication & Session Management

### Decision: JWT (Access + Refresh Tokens) with HTTP-only Cookies

**Rationale**:
- Stateless authentication reduces server memory footprint (constitution Principle V)
- HTTP-only cookies prevent XSS attacks (constitution Principle IV security)
- Refresh token rotation for long-lived sessions (user preference per FR-045)
- CSRF protection via SameSite cookie attribute
- FastAPI has excellent JWT support via `python-jose` library
- Session timeout configurable in Configuration entity

**Alternatives Considered**:
- **Server-side sessions**: Requires Redis/Memcached, adds deployment complexity - rejected
- **OAuth2**: Over-engineered for on-premises single-tenant deployment - rejected

**Implementation Notes**:
- Access token: 15-minute expiry, contains user_id + role (owner/admin/read-only)
- Refresh token: 7-day expiry, stored in HTTP-only cookie
- Password hashing: bcrypt with salt (industry standard, constitution Principle IV)
- Failed login rate limiting: 5 attempts per IP per 15 minutes
- Audit log: all login attempts, role changes, password resets

**Constitution Alignment**: Security requirements (Principle IV), RBAC implementation (FR-005)

---

## 7. Observability Stack

### Decision: Structured Logging (JSON) + Prometheus Metrics + Health Endpoints

**Rationale**:
- **Logging**: Python `logging` module with JSON formatter (constitution requirement for machine-parseable logs)
- **Metrics**: Prometheus Python client for FastAPI endpoints (request latency, error rates)
- **Health**: Custom `/health` and `/metrics` endpoints for operational monitoring
- No external dependencies required (on-premises constraint per FR-069-070)
- Logs to stdout (captured by Docker or systemd) for centralized collection if needed

**Alternatives Considered**:
- **ELK Stack**: Too heavy for on-premises deployment, requires Elasticsearch cluster - rejected
- **Grafana + Loki**: Adds operational complexity, overkill for initial deployment - rejected

**Implementation Notes**:
- Structured log format: `{"timestamp": "...", "level": "...", "module": "...", "message": "...", "context": {...}}`
- Log levels: ERROR (failures requiring attention), WARN (degraded state), INFO (state changes), DEBUG (development)
- Metrics exposed:
  - `ddms_device_readings_total{device_name}` - counter of successful readings
  - `ddms_device_errors_total{device_name, error_type}` - counter of device errors
  - `ddms_api_request_duration_seconds{endpoint, method}` - histogram of API latency
  - `ddms_active_devices` - gauge of online devices
- Health endpoint response:
  ```json
  {
    "status": "healthy",
    "database": "connected",
    "devices_online": 950,
    "devices_total": 1000,
    "uptime_seconds": 86400
  }
  ```

**Constitution Alignment**: Real-time observability (Principle II), structured logging requirement

---

## 8. Modbus Security Approach

### Decision: Secure Intranet Assumption + Optional VPN Tunneling

**Rationale**:
- Modbus TCP/IP protocol does not natively support TLS/SSL encryption
- Industrial PLCs rarely support encrypted Modbus variants
- On-premises intranet deployment (FR-069) provides physical network security
- Optional VPN tunneling (WireGuard, IPSec) for factory-to-server encryption if needed
- Focus security efforts on web application layer (HTTPS, authentication, authorization)

**Alternatives Considered**:
- **Modbus TLS wrappers**: Requires PLC support (rare), custom protocol handling - rejected
- **SSH tunneling**: Adds latency (unacceptable for 10s sampling), operational complexity - rejected

**Implementation Notes**:
- Document secure intranet requirements in deployment guide
- Web application MUST use HTTPS (TLS 1.3) for browser-to-server communication
- Modbus connections validated by IP whitelist in device configuration
- Network segmentation recommended: Modbus devices on separate VLAN from user network
- Optional VPN setup guide for multi-site deployments

**Constitution Alignment**: Security requirements (Principle IV) balanced with industrial constraints and performance needs (Principle V)

---

## 9. Real-Time Update Mechanism

### Decision: Server-Sent Events (SSE) over WebSocket

**Rationale**:
- SSE simpler than WebSocket (unidirectional server→client, no bidirectional needed)
- Automatic reconnection handling built into browser EventSource API
- Works over standard HTTP/HTTPS (no special firewall rules)
- Lower overhead than WebSocket handshake for frequent small updates
- FastAPI has excellent SSE support via `StreamingResponse`
- Falls back gracefully to polling if SSE unavailable

**Alternatives Considered**:
- **WebSocket**: Bidirectional overkill for dashboard updates, more complex reconnection logic - rejected
- **Polling**: Higher server load, increased latency - rejected as primary mechanism

**Implementation Notes**:
- SSE endpoint: `GET /api/devices/stream?device_ids=device1,device2,...`
- Event format: `data: {"device_name": "...", "value": 123.45, "timestamp": "...", "status": "normal"}\n\n`
- Client reconnects automatically on connection loss
- Server tracks active SSE connections per user (for rate limiting)
- Fallback to 10-second polling if SSE fails to connect after 3 attempts

**Constitution Alignment**: Real-time observability (Principle II), efficient resource use (Principle V)

---

## 10. Internationalization (i18n) Implementation

### Decision: react-i18next + Backend Message Catalog

**Rationale**:
- **Frontend**: react-i18next is industry standard for React i18n
- **Backend**: gettext-style message catalogs for API error messages
- Supports EN/CN per FR-042-043 with easy extension to additional languages (FR-276)
- Language preference stored per user (FR-045) in User entity
- Dynamic language switching without page reload (SC-013: <1s)

**Implementation Notes**:
- Frontend translation files: `src/locales/en-US.json`, `src/locales/zh-CN.json`
- Backend translations: `backend/locales/messages.po` compiled to `.mo` files
- Language detection: User.language_preference → Accept-Language header → default (en-US)
- Chart axis labels, units, tooltips translated via ECharts i18n config
- Date/time formatting: use `Intl.DateTimeFormat` with user's language

**Constitution Alignment**: User interface requirements (FR-046), language support assumption

---

## Summary of Resolved Clarifications

| Item | Decision | Rationale Summary |
|------|----------|-------------------|
| Modbus library | pymodbus 3.x | Async support, active maintenance, protocol coverage |
| Frontend framework | React 18 + TypeScript | Ecosystem, performance, type safety |
| Charting library | Apache ECharts | Performance with large datasets, i18n support |
| Time-series storage | PostgreSQL + TimescaleDB | Scalability, compression, retention automation |
| Frontend testing | Vitest + RTL + Playwright | Fast execution, coverage tooling |
| Authentication | JWT + HTTP-only cookies | Stateless, secure, session management |
| Observability | Structured JSON logs + Prometheus | Constitution requirement, operational visibility |
| Modbus security | Secure intranet + optional VPN | Industrial constraints, focus on app-layer security |
| Real-time updates | Server-Sent Events (SSE) | Simple, efficient, auto-reconnect |
| i18n | react-i18next + gettext | Standard tools, dynamic switching |

---

## Next Steps: Phase 1 Design

With all technical decisions resolved, Phase 1 will produce:
1. **data-model.md**: Entity schemas, relationships, validation rules
2. **contracts/**: OpenAPI specification for all API endpoints
3. **quickstart.md**: Local development setup and deployment guide
4. **Agent context update**: Add selected technologies to `.claude/` or `.cursor/` context files

All decisions align with constitution principles and support >=80% test coverage enforcement in Phase 2 task planning.

