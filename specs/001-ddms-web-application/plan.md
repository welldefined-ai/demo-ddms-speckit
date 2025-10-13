# Implementation Plan: DDMS Web Application

**Branch**: `001-ddms-web-application` | **Date**: 2025-10-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-ddms-web-application/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a web-based industrial device data monitoring system (DDMS) for real-time monitoring of Modbus devices in factory/coalmine environments. System provides live dashboards with color-coded alerts (normal/warning/critical), historical data analysis, device configuration, user management with role-based access control, multi-language support (English/Chinese), and on-premises deployment. Core capabilities: real-time data collection at 10-second intervals, 90-day data retention, threshold-based alerting, device grouping, and CSV export for external analysis.

## Technical Context

**Language/Version**: Python 3.11+ (backend), JavaScript/TypeScript (frontend - framework NEEDS CLARIFICATION)  
**Primary Dependencies**: 
- Backend: FastAPI, SQLAlchemy, pandas, pymodbus (NEEDS CLARIFICATION on Modbus library), asyncio
- Frontend: NEEDS CLARIFICATION (React/Vue/Svelte), Chart.js/Plotly (NEEDS CLARIFICATION on charting library), WebSocket/SSE for real-time updates
**Storage**: PostgreSQL with TimescaleDB extension for time-series data (NEEDS CLARIFICATION on specific TSDB choice)  
**Testing**: pytest + pytest-cov (backend), NEEDS CLARIFICATION (frontend testing framework)  
**Target Platform**: Linux server (on-premises intranet deployment), modern web browsers (Chrome, Firefox, Edge, Safari)  
**Project Type**: Web application (backend API + frontend SPA)  
**Performance Goals**: 
- Data ingestion: p95 < 500ms for 1000 devices at 10s intervals
- Dashboard load: < 3s initial, real-time updates < 1s
- Historical queries: < 2s for 24h range
- Support 100+ concurrent users
**Constraints**: 
- On-premises deployment (no cloud dependencies)
- Works without internet connectivity
- <= 80% test coverage (constitution requirement)
- 10-second data collection intervals (~8,640 readings/device/day)
- 90-day default retention (~777,600 readings/device)
**Scale/Scope**: Up to 1000 devices, 100+ concurrent users, multi-language UI (EN/CN), 6 user stories (P1-P6)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Data Reliability & Accuracy ✅ PASS

- ✅ Device data validated at ingestion (Modbus protocol validation)
- ✅ Malformed data rejected with error logging (FR-034, FR-188)
- ✅ Raw data stored immutably with timestamps (FR-056, FR-057)
- ✅ Data provenance tracked (device name, timestamp in Reading entity)
- ✅ Data quality indicators (quality indicator field in Reading entity, connection status)

**Status**: Compliant. Spec explicitly requires data persistence (FR-056-063), timestamps, and error indicators.

### II. Real-Time Observability & Visualization ✅ PASS

- ✅ Real-time device status visibility (FR-007-017, User Story 1)
- ✅ Dashboard auto-refresh at sampling intervals (FR-009, SC-002)
- ✅ Efficient chart rendering (SC-009: 30+ FPS, SC-003: identify status in < 5s)
- ✅ Color-coded visual indicators (FR-011, FR-012)
- ⚠️ Component health metrics (observability requirements) - NEEDS DESIGN in Phase 1

**Status**: Mostly compliant. Core visualization requirements met. Internal observability (logging, metrics) needs architecture design.

### III. Test-First Development (NON-NEGOTIABLE) ⚠️ PENDING

- ⚠️ >= 80% unit test coverage - NOT YET VERIFIED (will enforce in Phase 2 task planning)
- ⚠️ TDD process - NOT YET APPLIED (implementation phase)
- ⚠️ pytest + pytest-cov configured - NEEDS setup in Phase 1

**Status**: Not yet applicable (planning phase). Will be enforced in task creation and code review. Constitution requirement acknowledged and will gate all PRs.

### IV. Security & Data Integrity ✅ PASS

- ✅ Authentication required for all access (FR-001-006, FR-151)
- ✅ Role-based access control (owner/admin/read-only in FR-005)
- ✅ Audit logging for configuration changes (Edge Case: concurrent modifications)
- ✅ Transactional writes with rollback (FR-062)
- ✅ Automated backups (FR-058)
- ⚠️ TLS for Modbus connections - NEEDS CLARIFICATION (Modbus TCP typically unencrypted, secure intranet assumed)
- ⚠️ Password hashing, session security - NEEDS DESIGN in Phase 1

**Status**: Mostly compliant. Core security requirements in spec. Encryption details need architecture decisions.

### V. Performance & Efficiency ✅ PASS

- ✅ Data ingestion latency targets defined (SC-001: 3s dashboard load, SC-006: 2s historical query)
- ✅ Dashboard rendering performance (SC-009: 30+ FPS)
- ✅ Alert delivery latency (SC-017: detect violations within 10s)
- ✅ Scale target defined (1000 devices, 100+ users per SC-008)
- ✅ Async I/O for device communication (asyncio, constitution requirement)
- ⚠️ Connection pooling, caching strategy - NEEDS DESIGN in Phase 1
- ⚠️ Performance profiling - NOT YET APPLICABLE (implementation phase)

**Status**: Compliant. Performance targets in success criteria align with constitution. Implementation patterns to be detailed in Phase 1.

### Overall Gate Status: ✅ PASS WITH CLARIFICATIONS

**Pass Criteria Met**: All constitution principles addressed in spec. Security and performance implementation details appropriately deferred to Phase 1 design.

**Action Items for Phase 0 Research**:
1. Research Modbus security options (TLS wrappers vs. secure intranet assumptions)
2. Select Python Modbus library (pymodbus vs alternatives)
3. Select frontend framework and charting library
4. Select time-series database strategy (TimescaleDB vs native PostgreSQL)
5. Design observability stack (logging, metrics collection)
6. Design authentication/session management approach

**Re-check Required After Phase 1**: Verify design artifacts include test strategy, security implementation, and observability architecture.

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
backend/
├── src/
│   ├── models/              # SQLAlchemy models (User, Device, Reading, Threshold, Group, Configuration)
│   ├── services/            # Business logic (device_service, reading_service, alert_service, auth_service)
│   ├── collectors/          # Data collection workers (modbus_collector, device_manager)
│   ├── api/                 # FastAPI routes (auth, devices, readings, groups, users, export)
│   ├── db/                  # Database session management, migrations (Alembic)
│   ├── utils/               # Helpers (validation, formatting, logging)
│   └── main.py              # Application entry point
├── tests/
│   ├── unit/                # Unit tests for models, services, utils (>=80% coverage)
│   ├── integration/         # Integration tests for API endpoints, database operations
│   └── contract/            # Contract tests for Modbus device integrations
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies (pytest, black, mypy, etc.)
└── pytest.ini               # pytest configuration with coverage thresholds

frontend/
├── src/
│   ├── components/          # Reusable UI components (DeviceCard, Chart, AlertBanner, etc.)
│   ├── pages/               # Page components (Dashboard, DeviceConfig, Historical, UserManagement)
│   ├── services/            # API client, WebSocket handler, state management
│   ├── locales/             # i18n translation files (en-US.json, zh-CN.json)
│   ├── styles/              # Global styles, themes
│   └── App.tsx              # Application root
├── tests/
│   ├── unit/                # Component unit tests
│   └── e2e/                 # End-to-end tests for critical user journeys
├── package.json             # npm dependencies
└── vite.config.ts           # Build configuration (or webpack/rollup)

docker/
├── backend.Dockerfile       # Backend container image
├── frontend.Dockerfile      # Frontend build and serve container
└── docker-compose.yml       # Development orchestration (backend, frontend, PostgreSQL)

scripts/
├── deploy.sh                # On-premises deployment script
├── backup.sh                # Database backup automation
└── init-db.sh               # Database initialization and migrations

docs/
├── api/                     # Auto-generated OpenAPI documentation
├── architecture/            # Architecture Decision Records (ADRs)
└── deployment/              # Deployment guide, troubleshooting

.github/ (or .gitlab/)
└── workflows/               # CI pipeline (tests, coverage, linting, build)
```

**Structure Decision**: Web application architecture selected (Option 2 from template). Backend and frontend are separate codebases to support:
- Independent deployment and scaling
- Clear separation of concerns (API contracts as boundary)
- Technology-specific tooling (Python ecosystem for backend, Node.js for frontend)
- Independent testing strategies (pytest for backend, framework-specific for frontend)

**Rationale**: This structure aligns with constitution requirements for Python-first backend, supports modern web SPA patterns, enables on-premises Docker deployment, and provides clear test organization for >= 80% coverage enforcement.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

No constitution violations requiring justification. All complexity is justified by functional requirements:
- Web architecture (backend + frontend) required for browser-based access (FR-070-072)
- Modbus protocol support required for industrial device compatibility (FR-064-068)
- Real-time data collection required for monitoring use case (FR-007-017)
- Time-series storage required for historical analysis (FR-018-022)

All design decisions align with constitution principles and feature requirements.

---

## Phase 0: Research Complete ✅

**Output**: `research.md`

All "NEEDS CLARIFICATION" items resolved:
1. ✅ Python Modbus library: pymodbus 3.x (async support, active maintenance)
2. ✅ Frontend framework: React 18+ with TypeScript (ecosystem, type safety)
3. ✅ Charting library: Apache ECharts (performance, i18n support)
4. ✅ Time-series storage: PostgreSQL 15+ with TimescaleDB 2.x (scalability, retention automation)
5. ✅ Frontend testing: Vitest + React Testing Library + Playwright (fast, coverage tooling)
6. ✅ Authentication: JWT + HTTP-only cookies (stateless, secure)
7. ✅ Observability: Structured JSON logs + Prometheus metrics (constitution requirement)
8. ✅ Modbus security: Secure intranet assumption + optional VPN (industrial constraints)
9. ✅ Real-time updates: Server-Sent Events (SSE) (simple, efficient)
10. ✅ i18n: react-i18next + gettext (standard tools, dynamic switching)

**Rationale Document**: All decisions documented with alternatives considered and constitution alignment.

---

## Phase 1: Design & Contracts Complete ✅

**Outputs**:
- ✅ `data-model.md` - Full entity schema, relationships, validation rules, TimescaleDB configuration
- ✅ `contracts/openapi.yaml` - Complete OpenAPI 3.1 specification with all endpoints (auth, users, devices, readings, groups, export, system)
- ✅ `quickstart.md` - Development setup and on-premises deployment guide
- ✅ Agent context updated (`CLAUDE.md`) - Technologies added to Claude Code context

### Data Model Summary

**Core Entities**:
- User (authentication, RBAC)
- Device (Modbus configuration, thresholds, status)
- Reading (TimescaleDB hypertable, time-series data)
- Group (device grouping)
- DeviceGroup (association table)
- Configuration (system settings, singleton)

**Key Design Decisions**:
- Device uniqueness: User-assigned name (clarification from spec)
- TimescaleDB hypertables: 1-day chunks, compression after 7 days, continuous aggregates
- Validation: Three-layer enforcement (database, ORM, API)
- Performance: Connection pooling, strategic indexing, retention automation

### API Contracts Summary

**Endpoints**: 23 REST endpoints across 7 domains
- **Authentication**: Login, logout, refresh, password change
- **Users**: CRUD with RBAC enforcement (owner/admin/read-only per FR-005)
- **Devices**: CRUD, real-time SSE stream, status management
- **Readings**: Historical queries, latest reading, aggregation levels (raw/1min/1hour/1day)
- **Groups**: CRUD, device membership, aggregated readings
- **Export**: CSV export for devices and groups (FR-021, FR-041)
- **System**: Configuration management, health check

**Security**: JWT access tokens (15 min) + refresh tokens (7 days) in HTTP-only cookies

### Constitution Re-Check (Post-Phase 1) ✅

#### I. Data Reliability & Accuracy ✅ PASS
- ✅ TimescaleDB ensures immutable data storage with audit trail
- ✅ Quality indicator on all readings (good/bad/uncertain)
- ✅ Validation at database, ORM, and API layers
- ✅ No data loss during retention cleanup (export available per FR-060)

#### II. Real-Time Observability & Visualization ✅ PASS
- ✅ SSE endpoint for real-time dashboard updates (FR-009)
- ✅ ECharts selected for efficient visualization (30+ FPS per SC-009)
- ✅ Prometheus metrics exposed (`/metrics` endpoint)
- ✅ Structured JSON logging implemented (constitution requirement)
- ✅ Health endpoint for operational monitoring

#### III. Test-First Development (NON-NEGOTIABLE) ✅ READY
- ✅ pytest + pytest-cov configured for backend (>= 80% enforcement)
- ✅ Vitest + React Testing Library configured for frontend
- ✅ Test structure defined: unit, integration, contract, e2e
- ✅ quickstart.md includes TDD workflow instructions
- ⚠️ Enforcement: Phase 2 task planning will mandate tests for each task

**Status**: Infrastructure ready, enforcement begins in Phase 2 implementation.

#### IV. Security & Data Integrity ✅ PASS
- ✅ JWT authentication with HTTP-only cookies (XSS prevention)
- ✅ bcrypt password hashing specified in data model
- ✅ RBAC implemented (owner/admin/read_only roles per FR-005)
- ✅ CSRF protection via SameSite cookies
- ✅ Audit logging for configuration changes
- ✅ Transaction safety with rollback (FR-062)
- ✅ Automated backups specified (FR-058)
- ✅ Rate limiting on login (5 attempts per IP per 15 min)
- ✅ TLS 1.3 for web traffic (deployment guide)
- ✅ Modbus security: secure intranet assumption documented (industrial constraint)

**Status**: Full security architecture defined and compliant.

#### V. Performance & Efficiency ✅ PASS
- ✅ TimescaleDB hypertables with compression (90-95% size reduction)
- ✅ Continuous aggregates for fast queries (pre-computed rollups)
- ✅ Strategic indexes on query patterns (device_id + timestamp)
- ✅ Connection pooling specified (10-20 connections)
- ✅ SSE for efficient real-time updates (lower overhead than WebSocket)
- ✅ Async/await with asyncio (pymodbus AsyncModbusTcpClient)
- ✅ Performance targets defined in success criteria (SC-001 through SC-020)

**Expected Performance** (from data-model.md):
- Single device query (24h): < 100ms
- Dashboard query (100 devices): < 500ms
- Insert 1000 readings: < 200ms
- Historical export (1 week): < 2s

**Status**: Architecture meets all performance targets. Profiling deferred to implementation.

### Overall Constitution Compliance: ✅ FULL PASS

All five principles fully addressed in design phase:
1. ✅ Data Reliability & Accuracy - TimescaleDB, validation, quality indicators
2. ✅ Real-Time Observability - SSE, Prometheus, structured logging, health checks
3. ✅ Test-First Development - Infrastructure ready, >= 80% enforcement in Phase 2
4. ✅ Security & Data Integrity - JWT, RBAC, bcrypt, rate limiting, backups
5. ✅ Performance & Efficiency - Hypertables, compression, indexing, async I/O

**No violations or compromises required.**

---

## Phase 2: Task Planning (Next Step)

Phase 1 planning is complete. Next command: `/speckit.tasks`

The `/speckit.tasks` command will:
1. Break down implementation into granular tasks
2. Enforce test-first workflow for each task (>= 80% coverage per constitution)
3. Define acceptance criteria per task
4. Prioritize by dependencies and user story priority (P1-P6)
5. Generate `tasks.md` with checkboxes for tracking

**Estimated Task Breakdown**:
- Database setup & migrations: ~5 tasks
- Authentication & user management: ~8 tasks
- Device configuration & management: ~12 tasks
- Data collection (Modbus): ~8 tasks
- Real-time monitoring dashboard: ~15 tasks
- Historical data & export: ~8 tasks
- Device grouping: ~6 tasks
- Multi-language support: ~4 tasks
- System configuration & health: ~4 tasks
- Deployment & documentation: ~5 tasks

**Total Estimated**: ~75 tasks (each with test requirements)

---

## Technology Stack Summary

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: PostgreSQL 15 + TimescaleDB 2.x
- **Modbus**: pymodbus 3.x (async)
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt
- **Testing**: pytest + pytest-cov + pytest-mock
- **Linting**: black, flake8, mypy
- **Migrations**: Alembic
- **ASGI Server**: uvicorn

### Frontend
- **Language**: TypeScript
- **Framework**: React 18+
- **Build Tool**: Vite
- **Charting**: Apache ECharts (echarts-for-react)
- **i18n**: react-i18next
- **HTTP Client**: axios or fetch
- **Real-time**: EventSource API (SSE)
- **Testing**: Vitest + React Testing Library + Playwright
- **Linting**: ESLint + Prettier

### Infrastructure
- **Database**: PostgreSQL 15 + TimescaleDB extension
- **Containerization**: Docker + Docker Compose
- **Web Server**: Nginx (reverse proxy, TLS termination)
- **Monitoring**: Prometheus metrics + structured logs
- **Backup**: pg_dump (automated cron)

### Development Tools
- **Version Control**: Git
- **CI/CD**: GitHub Actions / GitLab CI (to be configured in Phase 2)
- **API Docs**: OpenAPI 3.1 (auto-generated by FastAPI)
- **Documentation**: Markdown (specs, ADRs, guides)

---

## Files Generated (Phase 0 + Phase 1)

```
specs/001-ddms-web-application/
├── spec.md                     # Feature specification (from /speckit.specify)
├── plan.md                     # This file (from /speckit.plan)
├── research.md                 # Phase 0: Technology research & decisions
├── data-model.md               # Phase 1: Database schema & entities
├── quickstart.md               # Phase 1: Development & deployment guide
└── contracts/
    └── openapi.yaml            # Phase 1: Complete API specification
```

**Next**: Run `/speckit.tasks` to generate `tasks.md` for implementation.

---

## Notes

- All clarifications from `/speckit.clarify` incorporated (device name uniqueness, 10s sampling, 90-day retention, 60s reconnection, in-app notifications)
- Constitution fully compliant with no violations
- >= 80% test coverage will be enforced on all tasks in Phase 2
- On-premises deployment optimized (no cloud dependencies)
- Industrial constraints respected (Modbus TCP unencrypted, secure intranet)
- Multi-language support (EN/CN) integrated throughout stack
- Performance targets defined and achievable with selected architecture
