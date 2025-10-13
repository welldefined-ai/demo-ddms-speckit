# Tasks: DDMS Web Application

**Input**: Design documents from `/specs/001-ddms-web-application/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml

**Tests**: Tests are REQUIRED per constitution Principle III (>= 80% test coverage mandatory)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US6, SETUP, FOUND, POLISH)
- Include exact file paths in descriptions

## Path Conventions
- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`
- Web application structure per plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] **T001** [P] [SETUP] Create backend directory structure (`backend/src/{models,services,collectors,api,db,utils}`, `backend/tests/{unit,integration,contract}`)
- [X] **T002** [P] [SETUP] Create frontend directory structure (`frontend/src/{components,pages,services,locales,styles}`, `frontend/tests/{unit,e2e}`)
- [X] **T003** [SETUP] Initialize Python 3.11+ backend with FastAPI dependencies in `backend/requirements.txt` (FastAPI, SQLAlchemy, pymodbus, python-jose, bcrypt, pytest, pytest-cov)
- [X] **T004** [SETUP] Initialize React 18+ frontend with TypeScript in `frontend/package.json` (React, TypeScript, Vite, ECharts, react-i18next, Vitest, Playwright)
- [X] **T005** [P] [SETUP] Configure black + flake8 + mypy in `backend/pyproject.toml` and `backend/.flake8`
- [X] **T006** [P] [SETUP] Configure ESLint + Prettier in `frontend/.eslintrc.js` and `frontend/.prettierrc`
- [X] **T007** [P] [SETUP] Configure pytest with coverage threshold >= 80% in `backend/pytest.ini`
- [X] **T008** [P] [SETUP] Configure Vitest with coverage in `frontend/vite.config.ts`
- [X] **T009** [P] [SETUP] Create Docker development environment (`docker/backend.Dockerfile`, `docker/frontend.Dockerfile`, `docker-compose.yml` with PostgreSQL + TimescaleDB)
- [X] **T010** [P] [SETUP] Create environment variable templates (`.env.example` for backend and frontend per quickstart.md)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] **T011** [FOUND] Setup Alembic migrations framework in `backend/src/db/` with initial migration script
- [X] **T012** [FOUND] Create TimescaleDB hypertable configuration in initial migration (`backend/src/db/migrations/versions/001_initial_schema.py`)
- [X] **T013** [P] [FOUND] Implement User model in `backend/src/models/user.py` with SQLAlchemy (username, password_hash, role enum, language_preference)
- [X] **T014** [P] [FOUND] Implement Device model in `backend/src/models/device.py` with Modbus fields per data-model.md
- [X] **T015** [P] [FOUND] Implement Reading model (TimescaleDB hypertable) in `backend/src/models/reading.py`
- [X] **T016** [P] [FOUND] Implement Group model in `backend/src/models/group.py`
- [X] **T017** [P] [FOUND] Implement DeviceGroup association model in `backend/src/models/device_group.py`
- [X] **T018** [P] [FOUND] Implement Configuration singleton model in `backend/src/models/configuration.py`
- [X] **T019** [FOUND] Create database session manager in `backend/src/db/session.py` with connection pooling
- [X] **T020** [P] [FOUND] Implement JWT authentication utilities in `backend/src/utils/auth.py` (create_access_token, verify_token, bcrypt helpers)
- [X] **T021** [P] [FOUND] Implement RBAC decorators in `backend/src/utils/rbac.py` (require_owner, require_admin, require_auth)
- [X] **T022** [P] [FOUND] Implement structured JSON logging in `backend/src/utils/logging.py` per constitution
- [X] **T023** [P] [FOUND] Create Pydantic request/response schemas in `backend/src/api/schemas.py` (UserSchema, DeviceSchema, ReadingSchema, GroupSchema, ConfigurationSchema per OpenAPI spec)
- [X] **T024** [FOUND] Setup FastAPI app in `backend/src/main.py` with middleware (CORS, exception handlers, request logging)
- [X] **T025** [P] [FOUND] Create base API router structure in `backend/src/api/routes.py`
- [X] **T026** [P] [FOUND] Implement error response schemas and handlers in `backend/src/api/errors.py`
- [X] **T027** [P] [FOUND] Create Prometheus metrics exporter in `backend/src/utils/metrics.py` (device_readings_total, api_request_duration_seconds, etc.)
- [X] **T028** [P] [FOUND] Setup React Router and base layout in `frontend/src/App.tsx`
- [X] **T029** [P] [FOUND] Create API client service in `frontend/src/services/api.ts` with auth token management
- [X] **T030** [P] [FOUND] Configure react-i18next in `frontend/src/services/i18n.ts` with EN/CN locale files
- [X] **T031** [P] [FOUND] Create translation files `frontend/src/locales/en-US.json` and `frontend/src/locales/zh-CN.json` (common strings)
- [X] **T032** [P] [FOUND] Create base UI components: `frontend/src/components/Layout.tsx`, `frontend/src/components/Header.tsx`, `frontend/src/components/Sidebar.tsx`
- [X] **T033** [FOUND] Run initial database migration and seed default owner account + configuration via `backend/src/db/init_default_data.py`
- [X] **T034** [P] [FOUND] Write unit tests for auth utilities achieving >= 80% coverage in `backend/tests/unit/test_auth.py`
- [X] **T035** [P] [FOUND] Write unit tests for all models with validation rules in `backend/tests/unit/models/test_*.py`
- [X] **T036** [FOUND] Verify foundation: Run all tests, confirm >= 80% coverage, start backend + frontend, verify health endpoint responds

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Real-Time Device Monitoring Dashboard (Priority: P1) 🎯 MVP

**Goal**: Operators can view live device readings with color-coded status indicators (normal/warning/critical) that auto-refresh at sampling intervals

**Independent Test**: Configure one Modbus device, verify current reading displays with correct color indicator, confirm auto-refresh works, verify threshold violations trigger visual warnings

### Tests for User Story 1

**NOTE: Write these tests FIRST, ensure they FAIL before implementation (TDD per constitution)**

- [X] **T037** [P] [US1] Contract test for GET `/api/devices/{device_id}/latest` in `backend/tests/contract/test_readings_api.py`
- [X] **T038** [P] [US1] Contract test for GET `/api/devices/stream` (SSE) in `backend/tests/contract/test_device_stream.py`
- [X] **T039** [P] [US1] Integration test for device status calculation (normal/warning/critical) in `backend/tests/integration/test_device_status.py`
- [X] **T040** [P] [US1] E2E test for dashboard load and real-time updates in `frontend/tests/e2e/dashboard.spec.ts`

### Implementation for User Story 1

- [X] **T041** [US1] Implement `get_device_status()` service logic in `backend/src/services/device_service.py` (calculate status from latest reading vs thresholds with hysteresis)
- [X] **T042** [US1] Implement GET `/api/devices/{device_id}/latest` endpoint in `backend/src/api/devices.py` returning Reading with status
- [X] **T043** [US1] Implement SSE endpoint GET `/api/devices/stream` in `backend/src/api/devices.py` with EventSource streaming per research.md
- [X] **T044** [P] [US1] Create DeviceCard component in `frontend/src/components/DeviceCard.tsx` with status color coding (green/yellow/red)
- [X] **T045** [P] [US1] Create Chart component wrapper in `frontend/src/components/Chart.tsx` using ECharts with threshold lines overlay
- [X] **T046** [P] [US1] Create AlertBanner component in `frontend/src/components/AlertBanner.tsx` for connection failure notifications
- [X] **T047** [US1] Implement SSE client in `frontend/src/services/sse.ts` with auto-reconnect (3 attempts, fallback to polling)
- [X] **T048** [US1] Create Dashboard page in `frontend/src/pages/Dashboard.tsx` integrating DeviceCard + Chart + real-time SSE updates
- [X] **T049** [US1] Add dashboard route to React Router in `frontend/src/App.tsx`
- [X] **T050** [US1] Implement tooltip logic in Chart component showing exact value, unit, timestamp on hover (FR-017)
- [X] **T051** [P] [US1] Write unit tests for device_service.get_device_status() >= 80% coverage in `backend/tests/unit/services/test_device_service.py`
- [X] **T052** [P] [US1] Write unit tests for DeviceCard component in `frontend/tests/unit/DeviceCard.test.tsx`
- [X] **T053** [P] [US1] Write unit tests for Chart component in `frontend/tests/unit/Chart.test.tsx`
- [X] **T054** [US1] Add translations for dashboard UI in `frontend/src/locales/en-US.json` and `zh-CN.json` (labels, status text, tooltips)

**Checkpoint**: User Story 1 complete - dashboard displays real-time device data with color-coded alerts and auto-refresh

---

## Phase 4: User Story 2 - Device Configuration and Threshold Management (Priority: P2)

**Goal**: Admins can add new Modbus devices, configure connection parameters, set thresholds, and manage device lifecycle

**Independent Test**: Add a Modbus device through configuration interface, verify connection succeeds, confirm data collection begins at configured interval

### Tests for User Story 2

- [X] **T055** [P] [US2] Contract test for POST `/api/devices` in `backend/tests/contract/test_device_crud.py`
- [X] **T056** [P] [US2] Contract test for PUT `/api/devices/{device_id}` in `backend/tests/contract/test_device_crud.py`
- [X] **T057** [P] [US2] Contract test for DELETE `/api/devices/{device_id}` in `backend/tests/contract/test_device_crud.py`
- [X] **T058** [P] [US2] Integration test for Modbus device connection validation in `backend/tests/integration/test_modbus_collector.py`
- [X] **T059** [P] [US2] E2E test for device creation workflow in `frontend/tests/e2e/device-config.spec.ts`

### Implementation for User Story 2

- [X] **T060** [US2] Implement device CRUD service methods in `backend/src/services/device_service.py` (create_device, update_device, delete_device with validation)
- [X] **T061** [US2] Implement POST `/api/devices` endpoint in `backend/src/api/devices.py` with admin/owner RBAC check
- [X] **T062** [US2] Implement PUT `/api/devices/{device_id}` endpoint in `backend/src/api/devices.py`
- [X] **T063** [US2] Implement DELETE `/api/devices/{device_id}` with keep_data query param in `backend/src/api/devices.py`
- [X] **T064** [US2] Implement GET `/api/devices` list endpoint with status filter in `backend/src/api/devices.py`
- [X] **T065** [US2] Create Modbus collector in `backend/src/collectors/modbus_collector.py` using pymodbus AsyncModbusTcpClient (connect, read_register, handle errors)
- [X] **T066** [US2] Create device manager in `backend/src/collectors/device_manager.py` (schedule collection per sampling_interval, handle reconnection policy)
- [X] **T067** [US2] Implement connection test service in `backend/src/services/device_service.py` (test_modbus_connection)
- [X] **T068** [P] [US2] Create DeviceForm component in `frontend/src/components/DeviceForm.tsx` with validation (name uniqueness, IP format, threshold ordering per data-model.md)
- [X] **T069** [P] [US2] Create DeviceList component in `frontend/src/components/DeviceList.tsx` with status indicators
- [X] **T070** [US2] Create DeviceConfig page in `frontend/src/pages/DeviceConfig.tsx` integrating DeviceList + DeviceForm
- [X] **T071** [US2] Add device config route with RBAC guard (admin/owner only) in `frontend/src/App.tsx`
- [X] **T072** [US2] Implement threshold validation UI in DeviceForm (warning_lower ≤ warning_upper, critical bounds checking)
- [X] **T073** [P] [US2] Write unit tests for device CRUD service >= 80% coverage in `backend/tests/unit/services/test_device_service.py`
- [X] **T074** [P] [US2] Write unit tests for Modbus collector in `backend/tests/unit/collectors/test_modbus_collector.py`
- [X] **T075** [P] [US2] Write unit tests for DeviceForm component in `frontend/tests/unit/DeviceForm.test.tsx`
- [X] **T076** [US2] Add translations for device configuration UI in locale files

**Checkpoint**: User Story 2 complete - admins can configure and manage devices with full CRUD operations

---

## Phase 5: User Story 3 - User Account Management (Priority: P3)

**Goal**: System owner can create and manage user accounts with role-based permissions (owner/admin/read-only)

**Independent Test**: Owner logs in, creates accounts for each role type, verifies role-based access restrictions work, confirms password changes function

### Tests for User Story 3

- [X] **T077** [P] [US3] Contract test for POST `/api/auth/login` in `backend/tests/contract/test_auth_api.py`
- [X] **T078** [P] [US3] Contract test for POST `/api/auth/logout` in `backend/tests/contract/test_auth_api.py`
- [X] **T079** [P] [US3] Contract test for POST `/api/auth/refresh` in `backend/tests/contract/test_auth_api.py`
- [X] **T080** [P] [US3] Contract test for POST `/api/users` in `backend/tests/contract/test_user_api.py`
- [X] **T081** [P] [US3] Contract test for DELETE `/api/users/{user_id}` in `backend/tests/contract/test_user_api.py`
- [X] **T082** [P] [US3] Integration test for RBAC enforcement in `backend/tests/integration/test_rbac.py`
- [X] **T083** [P] [US3] E2E test for login and user management in `frontend/tests/e2e/user-management.spec.ts`

### Implementation for User Story 3

- [X] **T084** [US3] Implement authentication service in `backend/src/services/auth_service.py` (login, logout, refresh_token, verify_password, rate_limiting)
- [X] **T085** [US3] Implement user service in `backend/src/services/user_service.py` (create_user, delete_user, change_password with bcrypt)
- [X] **T086** [US3] Implement POST `/api/auth/login` endpoint in `backend/src/api/auth.py` with rate limiting (5 attempts/15min)
- [X] **T087** [US3] Implement POST `/api/auth/logout` endpoint in `backend/src/api/auth.py` (clear refresh token cookie)
- [X] **T088** [US3] Implement POST `/api/auth/refresh` endpoint in `backend/src/api/auth.py` (rotate tokens)
- [X] **T089** [US3] Implement POST `/api/auth/change-password` endpoint in `backend/src/api/auth.py`
- [X] **T090** [US3] Implement POST `/api/users` endpoint in `backend/src/api/users.py` (owner only, cannot create owner role)
- [X] **T091** [US3] Implement GET `/api/users` endpoint in `backend/src/api/users.py` (owner/admin only)
- [X] **T092** [US3] Implement DELETE `/api/users/{user_id}` endpoint in `backend/src/api/users.py` (owner only, cannot delete owner)
- [X] **T093** [P] [US3] Create Login page in `frontend/src/pages/Login.tsx` with form validation
- [X] **T094** [P] [US3] Create UserManagement page in `frontend/src/pages/UserManagement.tsx` with user list and creation form
- [X] **T095** [P] [US3] Create PrivateRoute component in `frontend/src/components/PrivateRoute.tsx` for authentication check
- [X] **T096** [P] [US3] Create RoleGuard component in `frontend/src/components/RoleGuard.tsx` for role-based UI rendering
- [X] **T097** [US3] Implement auth context in `frontend/src/contexts/AuthContext.tsx` (store user, role, token refresh logic)
- [X] **T098** [US3] Add login route and protect other routes with PrivateRoute in `frontend/src/App.tsx`
- [X] **T099** [US3] Implement token refresh interceptor in API client (`frontend/src/services/api.ts`)
- [X] **T100** [P] [US3] Write unit tests for auth_service >= 80% coverage in `backend/tests/unit/services/test_auth_service.py`
- [X] **T101** [P] [US3] Write unit tests for user_service in `backend/tests/unit/services/test_user_service.py`
- [ ] **T102** [P] [US3] Write unit tests for Login component in `frontend/tests/unit/Login.test.tsx`
- [ ] **T103** [US3] Add translations for authentication and user management UI in locale files

**Checkpoint**: User Story 3 complete - multi-user access with RBAC fully functional

---

## Phase 6: User Story 4 - Historical Data Analysis and Export (Priority: P4)

**Goal**: Operators can analyze historical trends by selecting time ranges, zooming into periods, and exporting data to CSV

**Independent Test**: Accumulate historical data for one device, select various time ranges, verify zoom functionality, export to CSV with correct format

### Tests for User Story 4

- [ ] **T104** [P] [US4] Contract test for GET `/api/readings/{device_id}` with time range in `backend/tests/contract/test_historical_api.py`
- [ ] **T105** [P] [US4] Contract test for GET `/api/export/device/{device_id}` in `backend/tests/contract/test_export_api.py`
- [ ] **T106** [P] [US4] Integration test for TimescaleDB continuous aggregates in `backend/tests/integration/test_timescale_aggregates.py`
- [ ] **T107** [P] [US4] E2E test for historical view and CSV export in `frontend/tests/e2e/historical-analysis.spec.ts`

### Implementation for User Story 4

- [ ] **T108** [US4] Implement reading query service in `backend/src/services/reading_service.py` (query_readings with time_range, aggregate_level using continuous aggregates)
- [ ] **T109** [US4] Implement CSV export service in `backend/src/services/export_service.py` (generate CSV with timestamps, values, units per FR-021)
- [ ] **T110** [US4] Implement GET `/api/readings/{device_id}` endpoint in `backend/src/api/readings.py` with pagination
- [ ] **T111** [US4] Implement GET `/api/export/device/{device_id}` endpoint in `backend/src/api/export.py` returning CSV file
- [ ] **T112** [US4] Create continuous aggregate views in migration `backend/src/db/migrations/versions/002_continuous_aggregates.py` (1min, 1hour, 1day rollups)
- [ ] **T113** [P] [US4] Create HistoricalChart component in `frontend/src/components/HistoricalChart.tsx` with ECharts zoom/pan functionality
- [ ] **T114** [P] [US4] Create TimeRangePicker component in `frontend/src/components/TimeRangePicker.tsx` (last hour/24h/week/custom)
- [ ] **T115** [P] [US4] Create ExportButton component in `frontend/src/components/ExportButton.tsx` triggering CSV download
- [ ] **T116** [US4] Create Historical page in `frontend/src/pages/Historical.tsx` integrating HistoricalChart + TimeRangePicker + ExportButton
- [ ] **T117** [US4] Add historical route in `frontend/src/App.tsx`
- [ ] **T118** [US4] Implement data downsampling in HistoricalChart for large datasets (>1000 points)
- [ ] **T119** [P] [US4] Write unit tests for reading_service >= 80% coverage in `backend/tests/unit/services/test_reading_service.py`
- [ ] **T120** [P] [US4] Write unit tests for export_service in `backend/tests/unit/services/test_export_service.py`
- [ ] **T121** [P] [US4] Write unit tests for HistoricalChart component in `frontend/tests/unit/HistoricalChart.test.tsx`
- [ ] **T122** [US4] Add translations for historical analysis UI in locale files

**Checkpoint**: User Story 4 complete - historical data analysis and export fully functional

---

## Phase 7: User Story 5 - Device Grouping and Group Dashboards (Priority: P5)

**Goal**: Admins can organize devices into logical groups and view group-level dashboards with aggregated status

**Independent Test**: Create a group, assign multiple devices, verify group dashboard displays all device readings with group-level alert summary

### Tests for User Story 5

- [ ] **T123** [P] [US5] Contract test for POST `/api/groups` in `backend/tests/contract/test_group_api.py`
- [ ] **T124** [P] [US5] Contract test for PUT `/api/groups/{group_id}` (device membership) in `backend/tests/contract/test_group_api.py`
- [ ] **T125** [P] [US5] Contract test for GET `/api/groups/{group_id}/readings` in `backend/tests/contract/test_group_api.py`
- [ ] **T126** [P] [US5] Contract test for GET `/api/export/group/{group_id}` in `backend/tests/contract/test_export_api.py`
- [ ] **T127** [P] [US5] E2E test for group creation and group dashboard in `frontend/tests/e2e/device-groups.spec.ts`

### Implementation for User Story 5

- [ ] **T128** [US5] Implement group service in `backend/src/services/group_service.py` (create_group, update_membership, delete_group, get_group_status_summary)
- [ ] **T129** [US5] Implement POST `/api/groups` endpoint in `backend/src/api/groups.py`
- [ ] **T130** [US5] Implement GET `/api/groups` list endpoint in `backend/src/api/groups.py`
- [ ] **T131** [US5] Implement GET `/api/groups/{group_id}` with devices and alert summary in `backend/src/api/groups.py`
- [ ] **T132** [US5] Implement PUT `/api/groups/{group_id}` for device membership updates in `backend/src/api/groups.py`
- [ ] **T133** [US5] Implement DELETE `/api/groups/{group_id}` endpoint in `backend/src/api/groups.py`
- [ ] **T134** [US5] Implement GET `/api/groups/{group_id}/readings` with timestamp-aligned multi-device data in `backend/src/api/groups.py`
- [ ] **T135** [US5] Implement GET `/api/export/group/{group_id}` for multi-device CSV in `backend/src/api/export.py` (FR-041)
- [ ] **T136** [P] [US5] Create GroupForm component in `frontend/src/components/GroupForm.tsx` with device multi-select
- [ ] **T137** [P] [US5] Create GroupList component in `frontend/src/components/GroupList.tsx`
- [ ] **T138** [P] [US5] Create GroupDashboard component in `frontend/src/components/GroupDashboard.tsx` with alert summary counts
- [ ] **T139** [US5] Create Groups page in `frontend/src/pages/Groups.tsx` integrating GroupList + GroupForm + GroupDashboard
- [ ] **T140** [US5] Add groups route with admin/owner guard in `frontend/src/App.tsx`
- [ ] **T141** [P] [US5] Write unit tests for group_service >= 80% coverage in `backend/tests/unit/services/test_group_service.py`
- [ ] **T142** [P] [US5] Write unit tests for GroupDashboard component in `frontend/tests/unit/GroupDashboard.test.tsx`
- [ ] **T143** [US5] Add translations for groups UI in locale files

**Checkpoint**: User Story 5 complete - device grouping and group dashboards fully functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, system hardening, and deployment readiness

- [ ] **T157** [P] [POLISH] Implement system configuration service in `backend/src/services/config_service.py` (get_config, update_config per singleton pattern)
- [ ] **T158** [P] [POLISH] Implement GET `/api/system/config` endpoint in `backend/src/api/system.py`
- [ ] **T159** [P] [POLISH] Implement PUT `/api/system/config` endpoint in `backend/src/api/system.py` (owner only)
- [ ] **T160** [P] [POLISH] Implement GET `/api/system/health` endpoint in `backend/src/api/system.py` (no auth, returns status per research.md)
- [ ] **T161** [P] [POLISH] Implement GET `/metrics` Prometheus endpoint in `backend/src/main.py`
- [ ] **T162** [P] [POLISH] Create TimescaleDB retention policy in migration `backend/src/db/migrations/versions/003_retention_policy.py` (automatic cleanup per device.retention_days)
- [ ] **T163** [P] [POLISH] Create TimescaleDB compression policy in migration (compress chunks older than 7 days)
- [ ] **T164** [P] [POLISH] Implement device reconnection worker in `backend/src/collectors/device_manager.py` (60s retry, notify after 3 failures per clarification)
- [ ] **T164a** [P] [POLISH] Implement connection failure notification banner component in `frontend/src/components/ConnectionFailureBanner.tsx` and notification service in `backend/src/services/notification_service.py` (FR-034b)
- [ ] **T165** [P] [POLISH] Create Settings page in `frontend/src/pages/Settings.tsx` for system configuration (owner only)
- [ ] **T166** [P] [POLISH] Create production Docker Compose file `docker-compose.prod.yml` with optimized settings
- [ ] **T167** [P] [POLISH] Create production Dockerfiles with multi-stage builds (`docker/backend.Dockerfile`, `docker/frontend.Dockerfile`)
- [ ] **T168** [P] [POLISH] Create deployment script `scripts/deploy.sh` per quickstart.md
- [ ] **T169** [P] [POLISH] Create backup script `scripts/backup.sh` with pg_dump automation
- [ ] **T169a** [P] [POLISH] Configure automated backup schedule via cron job or systemd timer to run `scripts/backup.sh` daily at 2 AM (FR-058)
- [ ] **T170** [P] [POLISH] Create database initialization script `scripts/init-db.sh`
- [ ] **T171** [P] [POLISH] Create Nginx configuration template in `docker/nginx.conf` with TLS 1.3, SSE support, reverse proxy
- [ ] **T172** [P] [POLISH] Create CI pipeline configuration `.github/workflows/ci.yml` (run tests, check coverage >= 80%, lint)
- [ ] **T173** [P] [POLISH] Create comprehensive README.md in repository root with quickstart instructions
- [ ] **T174** [P] [POLISH] Create API documentation in `docs/api/` (OpenAPI spec + examples)
- [ ] **T175** [P] [POLISH] Create architecture decision records in `docs/architecture/` for key technology choices
- [ ] **T176** [P] [POLISH] Add error boundary component in `frontend/src/components/ErrorBoundary.tsx` for graceful React error handling
- [ ] **T177** [P] [POLISH] Implement loading states in all pages (skeleton screens or spinners)
- [ ] **T178** [P] [POLISH] Implement empty states for lists (no devices, no readings, no users)
- [ ] **T179** [P] [POLISH] Add form validation feedback (real-time field validation with error messages)
- [ ] **T180** [P] [POLISH] Implement responsive design adjustments for tablet access per FR-055
- [ ] **T181** [P] [POLISH] Add browser compatibility detection and warning per Edge Case
- [ ] **T182** [P] [POLISH] Performance optimization: implement data caching in frontend services
- [ ] **T183** [P] [POLISH] Security hardening: implement CSRF token validation
- [ ] **T184** [P] [POLISH] Security hardening: add Content-Security-Policy headers
- [ ] **T185** [P] [POLISH] Run full integration test suite across all user stories
- [ ] **T186** [P] [POLISH] Run E2E test suite for all critical user journeys (US1-US6)
- [ ] **T187** [POLISH] Final coverage check: verify >= 80% on both backend and frontend (constitution gate)
- [ ] **T188** [POLISH] Perform manual QA walkthrough per quickstart.md validation steps
- [ ] **T189** [POLISH] Load testing: verify 100 concurrent users and 1000 devices per SC-008
- [ ] **T190** [POLISH] Performance profiling: verify all success criteria targets met (SC-001 through SC-020)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories CAN proceed in parallel if team is staffed
  - OR sequentially in priority order: US1 (P1) → US2 (P2) → US3 (P3) → US4 (P4) → US5 (P5)
- **Polish (Phase 8)**: Depends on desired user stories being complete (minimum US1-US3 for MVP)

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Foundational - No other story dependencies
- **User Story 2 (P2)**: Depends only on Foundational - Integrates with US1 but independently testable
- **User Story 3 (P3)**: Depends only on Foundational - Required for multi-user access
- **User Story 4 (P4)**: Depends only on Foundational - Requires US1/US2 for device data to exist
- **User Story 5 (P5)**: Depends on US2 (devices must exist) - Can proceed after US2 complete

### Within Each User Story

1. Tests (T###) MUST be written and FAIL before implementation (TDD per constitution)
2. Models before services (if new entities needed)
3. Services before endpoints
4. Endpoints before frontend components
5. Core components before page integration
6. Unit tests after implementation to achieve >= 80% coverage
7. Story complete and checkpoint verified before moving to next priority

### Parallel Opportunities

**Within Setup (Phase 1)**:
- All tasks marked [P] (T001-T010) can run in parallel

**Within Foundational (Phase 2)**:
- Models (T013-T018) can run in parallel
- Auth utilities (T020-T021) can run in parallel with models
- Logging/metrics (T022, T027) can run in parallel
- Frontend base setup (T028-T032) can run in parallel with backend
- Tests (T034-T035) can run in parallel after code complete

**Across User Stories (Phase 3-7)**:
- Once Foundational complete, **entire user stories can be worked on in parallel by different developers**
- Example: Developer A does US1, Developer B does US3, Developer C does US4 simultaneously

**Within Each User Story**:
- All tests marked [P] can run in parallel
- All models marked [P] can run in parallel
- All independent components marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Write all tests for US1 together (TDD - these should FAIL initially):
Task T037: "Contract test for GET /api/devices/{device_id}/latest"
Task T038: "Contract test for GET /api/devices/stream (SSE)"
Task T039: "Integration test for device status calculation"
Task T040: "E2E test for dashboard load and real-time updates"

# After tests fail, launch all frontend components together:
Task T044: "Create DeviceCard component"
Task T045: "Create Chart component"
Task T046: "Create AlertBanner component"

# Launch all unit tests together after implementation:
Task T051: "Unit tests for device_service.get_device_status()"
Task T052: "Unit tests for DeviceCard component"
Task T053: "Unit tests for Chart component"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only)

**Minimum Viable Product delivers core monitoring + device management + authentication**

1. **Complete Phase 1: Setup** (T001-T010) - ~1 day
2. **Complete Phase 2: Foundational** (T011-T036) - ~3-5 days - **CRITICAL BLOCKING PHASE**
3. **Complete Phase 3: User Story 1** (T037-T054) - ~3-4 days - Real-time monitoring dashboard
4. **Complete Phase 4: User Story 2** (T055-T076) - ~3-4 days - Device configuration
5. **Complete Phase 5: User Story 3** (T077-T103) - ~3-4 days - User management
6. **Selective Polish** (T157-T164, T172-T173, T185-T190) - ~2-3 days - System hardening
7. **STOP and VALIDATE**: Test MVP independently, deploy to staging

**MVP Delivers**:
- ✅ Real-time device monitoring with alerts (US1)
- ✅ Device configuration and management (US2)
- ✅ Multi-user access with RBAC (US3)
- ✅ >= 80% test coverage (constitution requirement)
- ✅ Deployable on-premises system

**Total MVP Timeline**: ~15-20 days (single developer) or ~8-10 days (3 developers in parallel)

### Incremental Delivery (Full Feature Set)

1. **MVP** (US1-US3) → Deploy and gather feedback
2. **Add US4: Historical Analysis** → Deploy update (~3-4 days)
3. **Add US5: Device Grouping** → Deploy update (~3-4 days)
4. **Complete Polish Phase** → Final production deployment (~3-5 days)

**Full Timeline**: ~22-30 days (single developer) or ~11-15 days (3-4 developers in parallel)

### Parallel Team Strategy

**With 3 developers after Foundational phase completes:**

- **Developer A**: User Story 1 (Real-time Dashboard) - ~3-4 days
- **Developer B**: User Story 2 (Device Config) - ~3-4 days
- **Developer C**: User Story 3 (User Management) - ~3-4 days

**All three stories complete in ~4 days instead of 12 days**

Then proceed to US4-US5 with similar parallelization.

---

## Test Coverage Requirements

Per constitution Principle III (NON-NEGOTIABLE):

- **Backend**: >= 80% unit test coverage (enforced by pytest.ini)
- **Frontend**: >= 80% unit test coverage (enforced by vite.config.ts)
- **Contract tests**: All API endpoints must have contract tests
- **Integration tests**: All critical data pipelines and services
- **E2E tests**: All 6 user story critical journeys

**Coverage Checkpoints**:
- After Foundational phase: T036 verifies foundation >= 80%
- After each user story phase: Verify story-specific coverage
- Final gate: T187 verifies overall >= 80% before production

**TDD Workflow** (constitution requirement):
1. Write test that defines expected behavior (should FAIL)
2. Run test, verify it FAILS (red phase)
3. Implement minimum code to pass test (green phase)
4. Refactor while keeping tests passing
5. Achieve >= 80% coverage before task completion

---

## Task Count Summary

| Phase | Task Count | Story/Purpose |
|-------|------------|---------------|
| **Phase 1: Setup** | 10 tasks | Project initialization |
| **Phase 2: Foundational** | 26 tasks | **CRITICAL BLOCKER** - Core infrastructure |
| **Phase 3: User Story 1 (P1)** | 18 tasks | Real-time monitoring dashboard 🎯 MVP |
| **Phase 4: User Story 2 (P2)** | 22 tasks | Device configuration |
| **Phase 5: User Story 3 (P3)** | 27 tasks | User account management |
| **Phase 6: User Story 4 (P4)** | 19 tasks | Historical data analysis |
| **Phase 7: User Story 5 (P5)** | 21 tasks | Device grouping |
| **Phase 8: Polish** | 36 tasks | Cross-cutting concerns |
| **TOTAL** | **179 tasks** | Complete DDMS system |

**MVP Subset**: 83 tasks (Setup + Foundational + US1-US3 + Essential Polish)

---

## Parallel Opportunities Identified

- **Setup Phase**: 8 of 10 tasks can run in parallel
- **Foundational Phase**: 12 of 26 tasks can run in parallel
- **User Story Phases**: Entire user stories (US1-US5) can run in parallel after Foundational complete
- **Within User Stories**: ~40% of tasks within each story marked [P] for parallel execution
- **Polish Phase**: 34 of 36 tasks can run in parallel

**Maximum Parallelization**: With sufficient team size, after Foundational phase completes, all 5 user stories can be developed simultaneously, reducing timeline by ~80%.

---

## Notes

- **[P] tasks**: Different files, no dependencies - safe to parallelize
- **[Story] labels**: Track which user story each task belongs to (US1-US6, SETUP, FOUND, POLISH)
- **Constitution compliance**: >= 80% test coverage enforced at checkpoints (T036, T187)
- **TDD workflow**: Tests MUST fail before implementation (red → green → refactor)
- **Independent stories**: Each user story is independently testable at its checkpoint
- **MVP focus**: US1-US3 deliver core value, can ship without US4-US6
- **On-premises ready**: Polish phase includes full deployment automation
- **Modbus testing**: Use simulator per quickstart.md for development without physical devices

---

**Ready to begin**: Start with Phase 1 (Setup) and proceed sequentially through Foundational phase. Once Foundational completes, user stories can be implemented in priority order or in parallel based on team capacity! 🚀

