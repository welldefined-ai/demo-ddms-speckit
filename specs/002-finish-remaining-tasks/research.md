# Phase 0: Research & Technology Selection

**Feature**: Complete DDMS System Polish and Production Readiness
**Branch**: 002-finish-remaining-tasks
**Date**: 2025-10-16

## Overview

This document resolves all technology decisions required for Phase 8 (Polish & Cross-Cutting Concerns) implementation. Each decision includes rationale, alternatives considered, implementation notes, and alignment with constitution requirements. These decisions build upon the foundation established in feature 001-ddms-web-application and focus on production readiness, operational automation, security hardening, and user experience polish.

---

## 1. TimescaleDB Retention and Compression Policies

### Decision: TimescaleDB Built-In Retention and Compression Policies

**Rationale**:
- TimescaleDB provides native `add_retention_policy()` and `add_compression_policy()` functions eliminating need for custom cleanup logic
- Retention policies automatically delete data older than specified interval (e.g., 90 days) on scheduled basis
- Compression policies reduce storage by 70-95% for historical data using columnar compression
- Policies execute as background jobs without blocking queries or data ingestion
- Configuration via SQL migrations makes policies version-controlled and repeatable
- Performance overhead negligible (<1% CPU for typical 1000-device deployment)
- Integrates seamlessly with existing hypertables from feature 001

**Alternatives Considered**:
- **Manual DELETE queries via cron**: Requires custom scheduling logic, blocks transactions during deletion, no built-in compression - rejected
- **pg_cron + custom stored procedures**: Adds external dependency, more complex than native policies, harder to test - rejected
- **Application-level cleanup**: Inefficient for large datasets, requires table locks, no compression support - rejected
- **External compression tools (zstd, gzip)**: Cannot query compressed data, requires decompression before access - rejected

**Implementation Notes**:
- Create Alembic migration `003_retention_policy.py` adding retention policy:
  ```python
  op.execute("""
      SELECT add_retention_policy('readings', INTERVAL '90 days');
  """)
  ```
- Create migration `004_compression_policy.py` adding compression policy:
  ```python
  op.execute("""
      ALTER TABLE readings SET (
          timescaledb.compress,
          timescaledb.compress_segmentby = 'device_id',
          timescaledb.compress_orderby = 'timestamp DESC'
      );
      SELECT add_compression_policy('readings', INTERVAL '7 days');
  """)
  ```
- Retention policy runs daily at 2 AM server time (configurable via `schedule_interval`)
- Compression policy runs hourly checking for chunks older than 7 days
- Configurable retention period stored in `SystemConfiguration.data_retention_days` (default 90)
- Update retention policy dynamically when configuration changes:
  ```python
  SELECT remove_retention_policy('readings');
  SELECT add_retention_policy('readings', INTERVAL '{days} days');
  ```
- Warning banner displayed 24 hours before data deletion (FR-010)
- Compressed data remains queryable via TimescaleDB decompression on read

**Constitution Alignment**: Data Reliability (Principle I - automated retention without data loss within window), Performance & Efficiency (Principle V - 70-95% storage reduction per SC-023), Real-Time Observability (Principle II - policy execution logged for monitoring)

---

## 2. Prometheus Metrics Library for FastAPI

### Decision: prometheus-fastapi-instrumentator

**Rationale**:
- Purpose-built library for FastAPI with zero-configuration defaults for common metrics
- Automatically instruments all API endpoints with request duration, status codes, and concurrent requests
- Provides clean decorator-based API for custom business metrics (device readings, errors)
- Built on official `prometheus-client` library ensuring standard Prometheus exposition format
- Minimal performance overhead (<5ms per request for metrics collection)
- Metrics endpoint (`/metrics`) exposed without authentication per Prometheus best practices
- Response caching (10 seconds per FR-035) built-in via `should_respect_env_var` parameter
- Active maintenance (last update 2024) and wide adoption in FastAPI community

**Alternatives Considered**:
- **prometheus-client (direct)**: Requires manual middleware setup, no FastAPI-specific helpers, more boilerplate - rejected
- **starlette-prometheus**: Starlette-level instrumentation lacks FastAPI route details, less granular metrics - rejected
- **Custom metrics collector**: Reinventing wheel, testing burden, no standard exposition format - rejected

**Implementation Notes**:
- Install via `pip install prometheus-fastapi-instrumentator==6.1.0`
- Initialize in `main.py`:
  ```python
  from prometheus_fastapi_instrumentator import Instrumentator

  instrumentator = Instrumentator(
      should_group_status_codes=False,
      should_respect_env_var_existence=False,
      excluded_handlers=["/metrics", "/health"],
  )
  instrumentator.instrument(app).expose(app, endpoint="/metrics")
  ```
- Add custom metrics in `backend/src/utils/metrics.py`:
  ```python
  from prometheus_client import Counter, Histogram, Gauge

  device_readings_total = Counter(
      "ddms_device_readings_total",
      "Total device readings collected",
      ["device_name", "status"]
  )

  device_errors_total = Counter(
      "ddms_device_errors_total",
      "Total device collection errors",
      ["device_name", "error_type"]
  )

  active_devices = Gauge(
      "ddms_active_devices",
      "Number of currently connected devices"
  )

  active_sse_connections = Gauge(
      "ddms_active_sse_connections",
      "Number of active SSE connections"
  )

  db_query_duration = Histogram(
      "ddms_database_query_duration_seconds",
      "Database query execution time",
      ["query_type"]
  )
  ```
- Metrics endpoint responds in under 100ms per SC-009 (cached for 10 seconds)
- No authentication required for `/metrics` endpoint (standard Prometheus pattern)
- Rate limiting applied via Nginx (100 requests/minute per IP per FR-049)

**Constitution Alignment**: Real-Time Observability (Principle II - operational visibility via metrics), Performance & Efficiency (Principle V - minimal overhead, caching), Security (Principle IV - metrics don't expose sensitive data)

---

## 3. Nginx Configuration for TLS 1.3 + SSE Support

### Decision: Nginx 1.24+ with Optimized TLS and Proxy Configuration

**Rationale**:
- Nginx is industry-standard reverse proxy with proven performance for FastAPI backends
- TLS 1.3 support built-in since Nginx 1.13.0 (modern cipher suites, faster handshake)
- SSE long-lived connections require specific proxy buffering settings to prevent timeouts
- Can serve static frontend assets directly (React build output) reducing backend load
- Load balancing capability supports future horizontal scaling if needed
- HTTP/2 support improves frontend asset loading performance
- Security headers (CSP, HSTS, X-Frame-Options) configured centrally in Nginx
- Widely documented, available in all Linux distributions, minimal resource footprint

**Alternatives Considered**:
- **Traefik**: Modern but requires additional configuration complexity, less mature than Nginx for SSE - rejected
- **HAProxy**: Excellent load balancer but weaker at serving static files, steeper learning curve - rejected
- **Caddy**: Automatic HTTPS appealing but less industrial deployment experience, fewer operational guides - rejected
- **Direct HTTPS via Uvicorn**: No static file serving, limited header control, single point of failure - rejected

**Implementation Notes**:
- Install Nginx 1.24+ from official repositories
- Create `/etc/nginx/sites-available/ddms.conf`:
  ```nginx
  upstream fastapi_backend {
      server backend:8000;
      keepalive 64;
  }

  server {
      listen 443 ssl http2;
      server_name ddms.local;

      # TLS 1.3 Configuration
      ssl_certificate /etc/nginx/ssl/cert.pem;
      ssl_certificate_key /etc/nginx/ssl/key.pem;
      ssl_protocols TLSv1.3 TLSv1.2;
      ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
      ssl_prefer_server_ciphers on;
      ssl_session_cache shared:SSL:10m;
      ssl_session_timeout 10m;

      # Security Headers
      add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
      add_header X-Frame-Options "DENY" always;
      add_header X-Content-Type-Options "nosniff" always;
      add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self' wss:; frame-ancestors 'none';" always;

      # Frontend Static Assets
      location / {
          root /var/www/ddms/frontend;
          try_files $uri $uri/ /index.html;
          expires 1y;
          add_header Cache-Control "public, immutable";
      }

      # Backend API
      location /api/ {
          proxy_pass http://fastapi_backend;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;

          # Timeouts for API requests
          proxy_connect_timeout 10s;
          proxy_send_timeout 30s;
          proxy_read_timeout 30s;
      }

      # SSE Endpoint (special handling)
      location /api/devices/stream {
          proxy_pass http://fastapi_backend;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
          proxy_set_header Connection '';

          # SSE-specific settings (critical!)
          proxy_http_version 1.1;
          proxy_buffering off;
          proxy_cache off;
          chunked_transfer_encoding off;

          # Keep connection alive
          proxy_connect_timeout 10s;
          proxy_send_timeout 300s;
          proxy_read_timeout 300s;
      }

      # Health and Metrics (no auth required)
      location ~ ^/(health|metrics)$ {
          proxy_pass http://fastapi_backend;
          proxy_set_header Host $host;
          access_log off;  # Don't log health checks
      }
  }

  # HTTP to HTTPS redirect
  server {
      listen 80;
      server_name ddms.local;
      return 301 https://$server_name$request_uri;
  }
  ```
- Key SSE configuration items:
  - `proxy_buffering off;` - Critical for SSE event streaming
  - `proxy_cache off;` - Prevent caching of event stream
  - `chunked_transfer_encoding off;` - Disable chunked encoding for SSE
  - `proxy_read_timeout 300s;` - Long timeout for idle SSE connections
- TLS certificate setup documented in `docs/deployment/tls-setup.md`
- Self-signed certificates acceptable for internal deployments
- Rate limiting configured via Nginx `limit_req_zone` for FR-049

**Constitution Alignment**: Security (Principle IV - TLS 1.3, security headers per FR-044-048), Real-Time Observability (Principle II - SSE support for dashboard updates), Performance (Principle V - static asset caching, HTTP/2, connection pooling)

---

## 4. Docker Multi-Stage Builds for Production Images

### Decision: Multi-Stage Dockerfiles with Alpine Base and Non-Root User

**Rationale**:
- Multi-stage builds separate build dependencies from runtime dependencies reducing image size by 60-80%
- Alpine Linux base images (5MB) significantly smaller than Debian/Ubuntu (120MB+)
- Non-root user execution aligns with security best practices (Principle IV)
- Layer caching optimizes rebuild times (dependencies change less than application code)
- Production images contain only runtime essentials (no compilers, dev tools, test frameworks)
- Consistent reproducible builds across environments (local, CI, production)
- Docker Compose orchestrates backend + frontend + PostgreSQL + Nginx in production

**Alternatives Considered**:
- **Single-stage builds**: Includes unnecessary build tools in production, 2-3x larger images - rejected
- **Debian/Ubuntu base**: Larger images (slower pulls), more attack surface, slower startup - rejected
- **BuildKit with remote caching**: Adds infrastructure complexity for marginal benefit at 1000-device scale - rejected
- **Buildpacks (Heroku-style)**: Less control over final image, opinionated structure doesn't fit needs - rejected

**Implementation Notes**:
- Backend multi-stage Dockerfile (`docker/backend.Dockerfile`):
  ```dockerfile
  # Stage 1: Build dependencies
  FROM python:3.11-alpine AS builder
  WORKDIR /build

  # Install build dependencies
  RUN apk add --no-cache gcc musl-dev postgresql-dev libffi-dev

  # Install Python dependencies to virtual environment
  COPY requirements.txt .
  RUN python -m venv /opt/venv && \
      /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

  # Stage 2: Runtime
  FROM python:3.11-alpine
  WORKDIR /app

  # Install runtime dependencies only
  RUN apk add --no-cache libpq

  # Copy virtual environment from builder
  COPY --from=builder /opt/venv /opt/venv
  ENV PATH="/opt/venv/bin:$PATH"

  # Copy application code
  COPY backend/src ./src
  COPY backend/alembic.ini .

  # Create non-root user
  RUN addgroup -g 1001 -S ddms && \
      adduser -u 1001 -S ddms -G ddms && \
      chown -R ddms:ddms /app
  USER ddms

  # Health check
  HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
      CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

  EXPOSE 8000
  CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
  ```
- Frontend multi-stage Dockerfile (`docker/frontend.Dockerfile`):
  ```dockerfile
  # Stage 1: Build React app
  FROM node:20-alpine AS builder
  WORKDIR /build

  COPY frontend/package*.json ./
  RUN npm ci --only=production

  COPY frontend/ ./
  RUN npm run build

  # Stage 2: Serve via Nginx (handled by main nginx container)
  FROM alpine:3.19
  WORKDIR /app

  # Copy built assets only
  COPY --from=builder /build/dist ./dist

  # Create non-root user
  RUN addgroup -g 1001 -S ddms && \
      adduser -u 1001 -S ddms -G ddms && \
      chown -R ddms:ddms /app
  USER ddms

  # This stage just holds the built assets for volume mount
  CMD ["tail", "-f", "/dev/null"]
  ```
- Production Docker Compose (`docker/docker-compose.prod.yml`):
  ```yaml
  version: '3.8'
  services:
    db:
      image: timescale/timescaledb:2.13.0-pg15
      volumes:
        - postgres_data:/var/lib/postgresql/data
        - ./backups:/backups
      environment:
        POSTGRES_DB: ddms
        POSTGRES_USER: ${DB_USER}
        POSTGRES_PASSWORD: ${DB_PASSWORD}
      healthcheck:
        test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
        interval: 10s
        timeout: 5s
        retries: 5

    backend:
      build:
        context: ..
        dockerfile: docker/backend.Dockerfile
      depends_on:
        db:
          condition: service_healthy
      environment:
        DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/ddms
        SECRET_KEY: ${SECRET_KEY}
      deploy:
        replicas: 2
        update_config:
          parallelism: 1
          delay: 10s
        restart_policy:
          condition: on-failure

    nginx:
      image: nginx:1.25-alpine
      ports:
        - "443:443"
        - "80:80"
      volumes:
        - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
        - ./ssl:/etc/nginx/ssl:ro
        - frontend_dist:/var/www/ddms/frontend:ro
      depends_on:
        - backend

  volumes:
    postgres_data:
    frontend_dist:
  ```
- Image size targets: Backend <150MB, Frontend <50MB (vs 500MB+ single-stage)
- Build caching strategy: Dependencies layer cached separately from code
- Zero-downtime updates via `deploy.update_config.parallelism: 1`

**Constitution Alignment**: Security (Principle IV - non-root user, minimal attack surface), Performance (Principle V - smaller images, faster deployments), Development Workflow (reproducible builds, container isolation)

---

## 5. CI/CD Platform Selection

### Decision: GitHub Actions with pytest and Vitest Integration

**Rationale**:
- GitHub Actions native integration if repository hosted on GitHub (likely for open-source DDMS)
- Zero additional infrastructure required (no self-hosted Jenkins, GitLab runners)
- YAML-based workflow configuration version-controlled with code
- Rich ecosystem of pre-built actions (pytest, coverage, ESLint, Docker builds)
- Free tier sufficient for typical DDMS development workflow (2,000 minutes/month)
- Matrix builds enable testing across Python 3.11/3.12 and Node 18/20
- Coverage enforcement via `pytest-cov` (backend) and `vitest --coverage` (frontend)
- Pull request checks block merge if tests fail or coverage drops below 80%
- Automated Docker image builds and pushes to registry on tag creation

**Alternatives Considered**:
- **GitLab CI**: Excellent platform but requires GitLab hosting, self-hosted runners for on-premises, more setup - rejected
- **Jenkins**: Mature but requires dedicated server, complex pipeline scripting (Groovy), operational overhead - rejected
- **CircleCI**: Good platform but paid for private repos, less native integration than GitHub Actions - rejected
- **Drone CI**: Lightweight but smaller ecosystem, less documentation than GitHub Actions - rejected

**Implementation Notes**:
- Create `.github/workflows/ci.yml`:
  ```yaml
  name: CI Pipeline

  on:
    push:
      branches: [main, develop]
    pull_request:
      branches: [main]

  jobs:
    backend-tests:
      runs-on: ubuntu-latest
      strategy:
        matrix:
          python-version: ['3.11', '3.12']

      services:
        postgres:
          image: timescale/timescaledb:2.13.0-pg15
          env:
            POSTGRES_DB: ddms_test
            POSTGRES_USER: test
            POSTGRES_PASSWORD: test
          options: >-
            --health-cmd pg_isready
            --health-interval 10s
            --health-timeout 5s
            --health-retries 5

      steps:
        - uses: actions/checkout@v4

        - name: Set up Python ${{ matrix.python-version }}
          uses: actions/setup-python@v5
          with:
            python-version: ${{ matrix.python-version }}
            cache: 'pip'

        - name: Install dependencies
          run: |
            pip install -r backend/requirements.txt
            pip install -r backend/requirements-dev.txt

        - name: Run black formatter check
          run: black --check backend/src backend/tests

        - name: Run flake8 linter
          run: flake8 backend/src backend/tests

        - name: Run mypy type checker
          run: mypy backend/src

        - name: Run pytest with coverage
          env:
            DATABASE_URL: postgresql://test:test@localhost:5432/ddms_test
          run: |
            pytest backend/tests \
              --cov=backend/src \
              --cov-report=term-missing \
              --cov-report=xml \
              --cov-fail-under=80

        - name: Upload coverage to Codecov
          uses: codecov/codecov-action@v3
          with:
            files: ./coverage.xml
            flags: backend

    frontend-tests:
      runs-on: ubuntu-latest
      strategy:
        matrix:
          node-version: ['18', '20']

      steps:
        - uses: actions/checkout@v4

        - name: Set up Node.js ${{ matrix.node-version }}
          uses: actions/setup-node@v4
          with:
            node-version: ${{ matrix.node-version }}
            cache: 'npm'
            cache-dependency-path: frontend/package-lock.json

        - name: Install dependencies
          run: npm ci
          working-directory: frontend

        - name: Run ESLint
          run: npm run lint
          working-directory: frontend

        - name: Run Prettier check
          run: npm run format:check
          working-directory: frontend

        - name: Run Vitest with coverage
          run: npm run test:coverage
          working-directory: frontend

        - name: Check coverage threshold
          run: |
            COVERAGE=$(cat frontend/coverage/coverage-summary.json | jq '.total.lines.pct')
            if (( $(echo "$COVERAGE < 80" | bc -l) )); then
              echo "Coverage $COVERAGE% is below 80% threshold"
              exit 1
            fi

        - name: Upload coverage to Codecov
          uses: codecov/codecov-action@v3
          with:
            files: ./frontend/coverage/coverage-final.json
            flags: frontend

    contract-tests:
      runs-on: ubuntu-latest
      needs: [backend-tests]

      steps:
        - uses: actions/checkout@v4

        - name: Validate OpenAPI specification
          run: |
            npm install -g @apidevtools/swagger-cli
            swagger-cli validate docs/api/openapi.yaml

        - name: Run contract tests
          run: pytest backend/tests/contract --cov-fail-under=80

    docker-build:
      runs-on: ubuntu-latest
      needs: [backend-tests, frontend-tests]
      if: github.event_name == 'push' && github.ref == 'refs/heads/main'

      steps:
        - uses: actions/checkout@v4

        - name: Set up Docker Buildx
          uses: docker/setup-buildx-action@v3

        - name: Build backend image
          uses: docker/build-push-action@v5
          with:
            context: .
            file: docker/backend.Dockerfile
            push: false
            tags: ddms-backend:latest
            cache-from: type=gha
            cache-to: type=gha,mode=max

        - name: Build frontend image
          uses: docker/build-push-action@v5
          with:
            context: .
            file: docker/frontend.Dockerfile
            push: false
            tags: ddms-frontend:latest
            cache-from: type=gha
            cache-to: type=gha,mode=max
  ```
- CI pipeline completes in under 10 minutes per SC-015
- Coverage reports uploaded to Codecov for historical tracking
- Branch protection rules enforce CI passing before merge
- Matrix builds ensure compatibility across Python/Node versions

**Constitution Alignment**: Test-First Development (Principle III - automated coverage enforcement per NON-NEGOTIABLE requirement), Development Workflow (automated quality gates), Code Quality Standards (linting, formatting, type checking)

---

## 6. Database Backup Strategy

### Decision: pg_dump for Logical Backups with Compression

**Rationale**:
- pg_dump creates consistent logical backups without downtime or table locks
- Works seamlessly with TimescaleDB hypertables (no special handling needed)
- Compressed backups (gzip) reduce storage by 80-90% vs uncompressed
- Fast restore times (<10 minutes for typical 10GB database per SC-004)
- Point-in-time recovery not required for DDMS use case (retention policy handles data lifecycle)
- Simple operational model: single command, single output file, no complex archiving
- Aligns with on-premises constraint (no cloud storage integration needed)
- Automated via Python scheduler (APScheduler) running daily per configuration

**Alternatives Considered**:
- **Continuous WAL archiving (pg_basebackup)**: Provides point-in-time recovery but adds significant complexity, requires WAL storage management, overkill for 90-day retention model - rejected
- **pgBackRest**: Enterprise-grade but requires additional daemon, complex configuration, unnecessary for single-server deployment - rejected
- **Barman**: Excellent tool but Python-based agent adds dependency, operational overhead for benefit not needed - rejected
- **Docker volume snapshots**: Filesystem-level backup but requires storage backend support, less portable across environments - rejected

**Implementation Notes**:
- Create `BackupService` in `backend/src/services/backup_service.py`:
  ```python
  import subprocess
  from datetime import datetime
  from pathlib import Path
  from sqlalchemy.orm import Session
  from models.backup_job import BackupJob
  from core.config import settings

  class BackupService:
      def __init__(self, db: Session):
          self.db = db
          self.backup_dir = Path(settings.BACKUP_DIR)
          self.backup_dir.mkdir(parents=True, exist_ok=True)

      async def create_backup(self) -> BackupJob:
          """Execute pg_dump backup with compression."""
          timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
          backup_path = self.backup_dir / f"ddms_backup_{timestamp}.sql.gz"

          # Create BackupJob record
          job = BackupJob(
              start_time=datetime.utcnow(),
              status="running",
              backup_path=str(backup_path)
          )
          self.db.add(job)
          self.db.commit()

          try:
              # Execute pg_dump with compression
              cmd = [
                  "pg_dump",
                  "-h", settings.DB_HOST,
                  "-U", settings.DB_USER,
                  "-d", settings.DB_NAME,
                  "-F", "c",  # Custom format (compressed)
                  "-Z", "6",  # Compression level 6 (balance speed/size)
                  "-f", str(backup_path)
              ]

              result = subprocess.run(
                  cmd,
                  env={"PGPASSWORD": settings.DB_PASSWORD},
                  capture_output=True,
                  timeout=1800  # 30-minute timeout
              )

              if result.returncode != 0:
                  raise Exception(f"pg_dump failed: {result.stderr.decode()}")

              # Update job record
              job.end_time = datetime.utcnow()
              job.status = "success"
              job.file_size = backup_path.stat().st_size

              # Cleanup old backups (keep last 30)
              self._cleanup_old_backups(keep=30)

          except Exception as e:
              job.end_time = datetime.utcnow()
              job.status = "failed"
              job.error_message = str(e)
              raise

          finally:
              self.db.commit()

          return job

      def _cleanup_old_backups(self, keep: int = 30):
          """Remove old backup files, keeping last N."""
          backups = sorted(
              self.backup_dir.glob("ddms_backup_*.sql.gz"),
              key=lambda p: p.stat().st_mtime,
              reverse=True
          )
          for backup in backups[keep:]:
              backup.unlink()
  ```
- Schedule automated backups using APScheduler:
  ```python
  from apscheduler.schedulers.asyncio import AsyncIOScheduler
  from apscheduler.triggers.cron import CronTrigger

  scheduler = AsyncIOScheduler()

  # Schedule daily backup at 2 AM
  scheduler.add_job(
      backup_service.create_backup,
      trigger=CronTrigger.from_crontab(config.backup_schedule_cron),
      id="automated_backup"
  )
  ```
- Backup restoration via `pg_restore`:
  ```bash
  pg_restore -h localhost -U ddms -d ddms_restored -c ddms_backup_20251016_020000.sql.gz
  ```
- Manual backup trigger via API endpoint (owner-only): `POST /api/system/backup`
- Notification after 3 consecutive failures per FR-014
- Backup completion time <10 minutes for typical 10GB database per SC-004

**Constitution Alignment**: Data Reliability (Principle I - automated backups ensure recovery), Security (Principle IV - backup files stored with restricted permissions, optional encryption at rest), Performance (Principle V - compression reduces storage, minimal impact on operations)

---

## 7. CSRF Protection in FastAPI

### Decision: Double-Submit Cookie Pattern with CSRF Middleware

**Rationale**:
- Double-submit cookie pattern works seamlessly with JWT authentication (no server-side session required)
- FastAPI middleware intercepts state-changing requests (POST, PUT, DELETE) validating CSRF token
- CSRF token generated on login, stored in separate cookie (not HTTP-only) and included in request header
- Prevents cross-site request forgery while maintaining stateless authentication (Principle V)
- SameSite=Strict cookie attribute provides additional CSRF defense for modern browsers
- Compatible with SSE and API clients (token passed in X-CSRF-Token header)
- Minimal performance overhead (<1ms per request for token validation)

**Alternatives Considered**:
- **Synchronizer token pattern**: Requires server-side session storage (Redis/Memcached), contradicts stateless JWT design - rejected
- **Origin/Referer header validation**: Bypassed by some proxy configurations, less reliable than token - rejected
- **SameSite cookies only**: Insufficient for older browsers, doesn't protect API endpoints from authenticated users - rejected
- **FastAPI CSRF libraries (starlette-csrf)**: Abandoned project (last update 2021), prefer custom implementation - rejected

**Implementation Notes**:
- Create CSRF middleware in `backend/src/utils/csrf.py`:
  ```python
  from fastapi import Request, HTTPException
  from starlette.middleware.base import BaseHTTPMiddleware
  from secrets import token_urlsafe

  CSRF_COOKIE_NAME = "csrf_token"
  CSRF_HEADER_NAME = "X-CSRF-Token"

  class CSRFMiddleware(BaseHTTPMiddleware):
      async def dispatch(self, request: Request, call_next):
          # Skip GET, HEAD, OPTIONS (safe methods)
          if request.method in ["GET", "HEAD", "OPTIONS"]:
              return await call_next(request)

          # Skip /metrics, /health (public endpoints)
          if request.url.path in ["/metrics", "/health"]:
              return await call_next(request)

          # Validate CSRF token
          cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
          header_token = request.headers.get(CSRF_HEADER_NAME)

          if not cookie_token or not header_token:
              raise HTTPException(status_code=403, detail="CSRF token missing")

          if cookie_token != header_token:
              raise HTTPException(status_code=403, detail="CSRF token invalid")

          return await call_next(request)

  def generate_csrf_token() -> str:
      """Generate cryptographically secure CSRF token."""
      return token_urlsafe(32)
  ```
- Register middleware in `main.py`:
  ```python
  from utils.csrf import CSRFMiddleware

  app.add_middleware(CSRFMiddleware)
  ```
- Include CSRF token in login response:
  ```python
  from utils.csrf import generate_csrf_token, CSRF_COOKIE_NAME

  @router.post("/login")
  async def login(response: Response, credentials: LoginRequest):
      # ... authenticate user ...

      # Generate CSRF token
      csrf_token = generate_csrf_token()

      # Set CSRF cookie (NOT HTTP-only so JavaScript can read)
      response.set_cookie(
          key=CSRF_COOKIE_NAME,
          value=csrf_token,
          httponly=False,  # Must be readable by JavaScript
          secure=True,     # HTTPS only
          samesite="strict"
      )

      return {"access_token": access_token, "csrf_token": csrf_token}
  ```
- Frontend includes token in requests:
  ```typescript
  const csrfToken = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrf_token='))
      ?.split('=')[1];

  fetch('/api/devices', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfToken
      },
      body: JSON.stringify(deviceData)
  });
  ```
- CSRF protection enforced per FR-044
- Token rotation on each login (old tokens invalidated)

**Constitution Alignment**: Security (Principle IV - CSRF protection per FR-044, aligns with authentication model), Performance (Principle V - stateless validation, no session storage overhead)

---

## 8. React Error Boundaries

### Decision: Per-Route Error Boundaries with Fallback UI

**Rationale**:
- React error boundaries catch component errors preventing entire application crash
- Per-route placement isolates failures to affected page (dashboard error doesn't break settings page)
- Fallback UI displays user-friendly error message with refresh/home navigation options
- Error details logged to backend for monitoring and debugging (non-intrusive to user)
- Integrates with existing React 18 application structure without refactoring
- Supports error recovery via component key reset (user can retry without page reload)
- Aligns with graceful degradation principle (partial failure doesn't affect working features)

**Alternatives Considered**:
- **Global error boundary only**: Single failure point, entire app becomes unavailable, poor user experience - rejected
- **Error boundaries per component**: Over-engineering, too granular, complicates state management - rejected
- **try-catch in components**: Doesn't catch rendering errors or lifecycle errors, incomplete solution - rejected
- **window.onerror handler**: Catches unhandled errors but can't provide React-specific fallback UI - rejected

**Implementation Notes**:
- Create error boundary component in `frontend/src/components/ErrorBoundary.tsx`:
  ```typescript
  import React, { Component, ReactNode } from 'react';

  interface Props {
      children: ReactNode;
      fallback?: ReactNode;
      onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  }

  interface State {
      hasError: boolean;
      error: Error | null;
  }

  export class ErrorBoundary extends Component<Props, State> {
      constructor(props: Props) {
          super(props);
          this.state = { hasError: false, error: null };
      }

      static getDerivedStateFromError(error: Error): State {
          return { hasError: true, error };
      }

      componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
          console.error('ErrorBoundary caught:', error, errorInfo);

          // Log to backend monitoring
          fetch('/api/errors', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                  error: error.toString(),
                  stack: errorInfo.componentStack,
                  url: window.location.href,
                  timestamp: new Date().toISOString()
              })
          }).catch(console.error);

          // Call optional error handler
          this.props.onError?.(error, errorInfo);
      }

      render() {
          if (this.state.hasError) {
              return this.props.fallback || (
                  <div className="error-fallback">
                      <h2>Something went wrong</h2>
                      <p>We've been notified and are working to fix the issue.</p>
                      <button onClick={() => window.location.reload()}>
                          Refresh Page
                      </button>
                      <button onClick={() => window.location.href = '/'}>
                          Go Home
                      </button>
                      {process.env.NODE_ENV === 'development' && (
                          <details>
                              <summary>Error Details</summary>
                              <pre>{this.state.error?.stack}</pre>
                          </details>
                      )}
                  </div>
              );
          }

          return this.props.children;
      }
  }
  ```
- Wrap routes with error boundaries in `App.tsx`:
  ```typescript
  import { ErrorBoundary } from './components/ErrorBoundary';

  function App() {
      return (
          <Router>
              <Routes>
                  <Route path="/dashboard" element={
                      <ErrorBoundary fallback={<DashboardErrorFallback />}>
                          <Dashboard />
                      </ErrorBoundary>
                  } />
                  <Route path="/devices" element={
                      <ErrorBoundary fallback={<DevicesErrorFallback />}>
                          <DeviceList />
                      </ErrorBoundary>
                  } />
                  <Route path="/settings" element={
                      <ErrorBoundary fallback={<SettingsErrorFallback />}>
                          <Settings />
                      </ErrorBoundary>
                  } />
              </Routes>
          </Router>
      );
  }
  ```
- Custom fallback UIs per route (optional, falls back to default):
  ```typescript
  const DashboardErrorFallback = () => (
      <div className="dashboard-error">
          <h2>Dashboard Temporarily Unavailable</h2>
          <p>Unable to load device data. Please check your connection.</p>
          <button onClick={() => window.location.reload()}>Retry</button>
      </div>
  );
  ```
- Error boundary doesn't catch:
  - Event handlers (use try-catch inside handlers)
  - Asynchronous code (use async error handling)
  - Server-side rendering (SSR not used in DDMS)
- Error details logged to backend `/api/errors` endpoint for monitoring
- Fallback UI displays per FR-039

**Constitution Alignment**: Real-Time Observability (Principle II - error logging for monitoring), User Interface (graceful degradation improves UX per FR-039), Data Reliability (Principle I - errors don't cause data loss or corruption)

---

## 9. Tablet Responsive Design

### Decision: 768px Breakpoint with 44px Minimum Touch Targets

**Rationale**:
- 768px breakpoint aligns with iPad and Android tablet portrait mode (industry standard)
- 44x44px minimum touch target follows iOS Human Interface Guidelines (44pt) and Material Design (48dp)
- CSS Grid and Flexbox provide fluid layouts adapting to tablet screen sizes without media query explosion
- Touch-friendly controls include larger buttons, increased padding, swipe gestures for charts
- Responsive design maintains desktop functionality (no features removed for tablets)
- ECharts supports touch events natively (pinch-zoom, swipe for time range selection)
- Viewport meta tag prevents unwanted scaling on touch devices

**Alternatives Considered**:
- **Mobile-first design (320px breakpoint)**: DDMS is operational monitoring system not suited for phone screens, wasted effort - rejected
- **Separate mobile app**: Requires native development (Swift/Kotlin), maintenance overhead, feature parity challenges - rejected
- **Desktop-only (no responsive)**: Excludes plant managers using tablets for floor inspections, poor accessibility - rejected
- **1024px breakpoint**: Too large, excludes many tablets in portrait mode (768px is standard) - rejected

**Implementation Notes**:
- Add viewport meta tag in `frontend/index.html`:
  ```html
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  ```
- Create tablet styles in `frontend/src/styles/tablet.css`:
  ```css
  /* Tablet breakpoint */
  @media (min-width: 768px) and (max-width: 1024px) {
      /* Larger touch targets */
      button, a.button {
          min-height: 44px;
          min-width: 44px;
          padding: 12px 24px;
          font-size: 16px;
      }

      /* Responsive grid for device cards */
      .device-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 20px;
      }

      /* Touch-friendly form inputs */
      input, select, textarea {
          min-height: 44px;
          padding: 12px;
          font-size: 16px;  /* Prevents zoom on iOS */
      }

      /* Collapsible sidebar on tablet */
      .sidebar {
          position: fixed;
          left: -280px;
          transition: left 0.3s ease;
      }

      .sidebar.open {
          left: 0;
      }

      /* Larger chart controls */
      .chart-controls button {
          min-width: 60px;
          min-height: 44px;
      }

      /* Touch-friendly table rows */
      .data-table tbody tr {
          height: 56px;
      }
  }

  /* Touch device detection (pointer: coarse) */
  @media (pointer: coarse) {
      /* Increase padding for all interactive elements */
      button, a, .clickable {
          padding: 12px;
      }

      /* Remove hover effects on touch devices */
      button:hover {
          /* No hover state - use :active instead */
      }

      button:active {
          transform: scale(0.95);
          background-color: var(--color-primary-dark);
      }
  }
  ```
- ECharts touch configuration:
  ```typescript
  const chartOptions = {
      // ... existing options ...
      toolbox: {
          feature: {
              dataZoom: {
                  yAxisIndex: 'none',
                  brushStyle: {
                      borderWidth: 2,
                      borderColor: '#007bff'
                  }
              }
          }
      },
      // Enable touch zoom and pan
      dataZoom: [{
          type: 'inside',
          filterMode: 'none',
          // Touch-friendly zoom
          zoomOnMouseWheel: 'shift',
          moveOnMouseMove: 'ctrl'
      }]
  };
  ```
- Touch target size verification via browser DevTools (iPhone/iPad simulator)
- Responsive design supports tablets per FR-040-041
- Touch-friendly controls achieve 95%+ tap recognition per SC-014

**Constitution Alignment**: User Interface (accessibility for tablet users per FR-040-041), Real-Time Observability (Principle II - visualization works on tablets for mobile monitoring), Performance (Principle V - responsive CSS optimized for rendering speed)

---

## 10. Browser Compatibility Detection

### Decision: User-Agent Parsing with Feature Detection Fallback

**Rationale**:
- User-Agent parsing provides browser name and version for compatibility warnings
- Feature detection (checking for ES2020 features, EventSource, CSS Grid) confirms actual capability
- Warning banner displays on outdated browsers (Chrome <90, Firefox <88, Safari <14, Edge <90)
- Detection runs once on page load with result cached in sessionStorage (minimal overhead)
- Supported browsers list documented in help section and displayed in warning
- Graceful degradation: unsupported browsers show warning but app remains functional where possible
- No browser detection library dependencies (lightweight custom implementation)

**Alternatives Considered**:
- **Feature detection only**: Provides capability check but no specific browser/version for troubleshooting, poor user guidance - rejected
- **modernizr.js**: Comprehensive but adds 30KB bundle, overkill for checking few features - rejected
- **browserslist + autoprefixer**: Build-time tool, doesn't provide runtime detection for warnings - rejected
- **Block old browsers entirely**: Too aggressive, may alienate users with legitimate constraints, reduces accessibility - rejected

**Implementation Notes**:
- Create browser detection utility in `frontend/src/utils/browserDetection.ts`:
  ```typescript
  interface BrowserInfo {
      name: string;
      version: number;
      isSupported: boolean;
      missingFeatures: string[];
  }

  export function detectBrowser(): BrowserInfo {
      const ua = navigator.userAgent;
      let name = 'Unknown';
      let version = 0;

      // Parse User-Agent for major browsers
      if (ua.includes('Chrome/') && !ua.includes('Edg/')) {
          name = 'Chrome';
          version = parseInt(ua.split('Chrome/')[1].split('.')[0]);
      } else if (ua.includes('Firefox/')) {
          name = 'Firefox';
          version = parseInt(ua.split('Firefox/')[1].split('.')[0]);
      } else if (ua.includes('Safari/') && !ua.includes('Chrome/')) {
          name = 'Safari';
          const versionMatch = ua.match(/Version\/([\d.]+)/);
          version = versionMatch ? parseInt(versionMatch[1]) : 0;
      } else if (ua.includes('Edg/')) {
          name = 'Edge';
          version = parseInt(ua.split('Edg/')[1].split('.')[0]);
      }

      // Feature detection
      const missingFeatures: string[] = [];

      // Check ES2020 features
      if (typeof BigInt === 'undefined') {
          missingFeatures.push('BigInt');
      }
      if (typeof Promise.allSettled !== 'function') {
          missingFeatures.push('Promise.allSettled');
      }
      if (typeof String.prototype.matchAll !== 'function') {
          missingFeatures.push('String.matchAll');
      }

      // Check browser APIs
      if (typeof EventSource === 'undefined') {
          missingFeatures.push('Server-Sent Events');
      }
      if (!window.CSS || !CSS.supports('display', 'grid')) {
          missingFeatures.push('CSS Grid');
      }
      if (typeof WebSocket === 'undefined') {
          missingFeatures.push('WebSocket');
      }

      // Determine support based on version and features
      const minVersions: Record<string, number> = {
          Chrome: 90,
          Firefox: 88,
          Safari: 14,
          Edge: 90
      };

      const isSupported =
          name in minVersions &&
          version >= minVersions[name] &&
          missingFeatures.length === 0;

      return { name, version, isSupported, missingFeatures };
  }

  export function shouldShowWarning(): boolean {
      // Check sessionStorage cache
      const cached = sessionStorage.getItem('browserCheckDone');
      if (cached) return false;

      const browser = detectBrowser();
      sessionStorage.setItem('browserCheckDone', 'true');

      return !browser.isSupported;
  }
  ```
- Create browser warning component in `frontend/src/components/BrowserWarning.tsx`:
  ```typescript
  import React, { useState, useEffect } from 'react';
  import { detectBrowser, shouldShowWarning } from '../utils/browserDetection';

  export const BrowserWarning: React.FC = () => {
      const [show, setShow] = useState(false);
      const [browser, setBrowser] = useState(detectBrowser());

      useEffect(() => {
          if (shouldShowWarning()) {
              setShow(true);
              setBrowser(detectBrowser());
          }
      }, []);

      if (!show) return null;

      return (
          <div className="browser-warning-banner">
              <div className="warning-content">
                  <h3>Browser Compatibility Warning</h3>
                  <p>
                      Your browser ({browser.name} {browser.version}) may not support all features.
                      For the best experience, please use:
                  </p>
                  <ul>
                      <li>Chrome 90 or later</li>
                      <li>Firefox 88 or later</li>
                      <li>Safari 14 or later</li>
                      <li>Edge 90 or later</li>
                  </ul>
                  {browser.missingFeatures.length > 0 && (
                      <details>
                          <summary>Missing features</summary>
                          <ul>
                              {browser.missingFeatures.map(feature => (
                                  <li key={feature}>{feature}</li>
                              ))}
                          </ul>
                      </details>
                  )}
                  <button onClick={() => setShow(false)}>Dismiss</button>
              </div>
          </div>
      );
  };
  ```
- Include warning in app root:
  ```typescript
  function App() {
      return (
          <>
              <BrowserWarning />
              <Router>
                  {/* ... routes ... */}
              </Router>
          </>
      );
  }
  ```
- Browser compatibility warning displays per FR-042
- Supported browser list maintained in documentation
- Warning dismissible but reappears on new session

**Constitution Alignment**: User Interface (proactive compatibility guidance per FR-042), Real-Time Observability (Principle II - users informed of potential limitations), Security (Principle IV - modern browsers have better security features)

---

## Summary of Resolved Clarifications

| Topic | Decision | Rationale Summary |
|-------|----------|-------------------|
| TimescaleDB Policies | Native retention + compression policies | Automatic data lifecycle management, 70-95% storage reduction, no custom code |
| Prometheus Metrics | prometheus-fastapi-instrumentator | FastAPI-native, zero-config defaults, minimal overhead, standard exposition |
| Nginx Configuration | Nginx 1.24+ with TLS 1.3 + SSE optimizations | Industry-standard proxy, TLS 1.3 support, SSE-specific buffering config, security headers |
| Docker Multi-Stage | Alpine base with multi-stage builds | 60-80% image size reduction, non-root user, layer caching, reproducible builds |
| CI/CD Platform | GitHub Actions with pytest/Vitest | Zero infrastructure, native GitHub integration, matrix builds, coverage enforcement |
| Database Backups | pg_dump with compression | Logical backups, no downtime, 80-90% compression, simple restore, automated scheduling |
| CSRF Protection | Double-submit cookie pattern | Stateless (aligns with JWT), FastAPI middleware, SameSite cookies, <1ms overhead |
| Error Boundaries | Per-route React error boundaries | Isolates failures, fallback UI, error logging, graceful degradation |
| Tablet Design | 768px breakpoint, 44px touch targets | iPad/Android standard, iOS HIG compliance, touch-friendly controls, ECharts touch support |
| Browser Detection | User-Agent parsing + feature detection | Browser version identification, ES2020/API feature checks, compatibility warnings |

---

## Next Steps: Phase 1 Design

With all technical decisions resolved, Phase 1 will produce:

1. **data-model.md**: Entity schemas for SystemConfiguration (enhanced), BackupJob (new), ConnectionFailureNotification (new), with relationships and validation rules
2. **contracts/openapi.yaml**: API endpoint specifications for system configuration, health check, Prometheus metrics, backup management, connection failure notifications
3. **quickstart.md**: Production deployment guide with Docker Compose setup, TLS configuration, automated deployment scripts, backup/restore procedures, CI pipeline setup
4. **Agent context update**: Add selected technologies (prometheus-fastapi-instrumentator, nginx, GitHub Actions, pg_dump, APScheduler, multi-stage Docker builds) to project context

All decisions align with constitution principles:
- **Principle I (Data Reliability)**: Automated backups, retention enforcement, transactional migrations
- **Principle II (Real-Time Observability)**: Prometheus metrics, health checks, error logging, structured logs
- **Principle III (Test-First Development)**: CI pipeline enforces >=80% coverage, pytest/Vitest integration
- **Principle IV (Security)**: TLS 1.3, CSRF protection, CSP headers, non-root containers, rate limiting
- **Principle V (Performance)**: Compression (70-95%), metrics caching, multi-stage builds, async operations

Phase 2 task generation (`/speckit.tasks`) will create ~40-50 actionable tasks completing all 34 remaining Phase 8 items while maintaining constitution compliance throughout implementation.
