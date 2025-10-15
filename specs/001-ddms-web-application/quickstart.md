# Quickstart Guide: DDMS Web Application

**Feature**: DDMS Web Application  
**Branch**: 001-ddms-web-application  
**Date**: 2025-10-10

## Overview

This guide provides step-by-step instructions for local development setup and on-premises deployment of the Device Data Monitoring System (DDMS).

---

## Prerequisites

### Development Environment

- **Python**: 3.11+ ([python.org](https://python.org))
- **Node.js**: 18+ LTS ([nodejs.org](https://nodejs.org))
- **Docker**: 24+ with Docker Compose ([docker.com](https://docker.com))
- **Git**: For version control
- **PostgreSQL**: 15+ (can use Docker, see below)
- **Text Editor/IDE**: VS Code, PyCharm, or similar

### System Requirements

- **OS**: Linux (Ubuntu 20.04+, RHEL 8+), macOS 12+, Windows 10+ with WSL2
- **RAM**: Minimum 8GB (16GB recommended for development)
- **Disk**: Minimum 20GB free space
- **Network**: Access to internal network with Modbus devices

---

## Quick Start (Docker Development)

The fastest way to get started is using Docker Compose for all services.

### 1. Clone Repository

```bash
git clone https://github.com/your-org/demo-monitor.git
cd demo-monitor
git checkout 001-ddms-web-application
```

### 2. Start All Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL 15 with TimescaleDB extension (port 5432)
- Backend API server (port 8000)
- Frontend development server (port 3000)

### 3. Initialize Database

```bash
docker-compose exec backend python -m alembic upgrade head
docker-compose exec backend python -m src.db.init_default_data
```

### 4. Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: http://localhost:8000/api/system/health

### 5. Default Login Credentials

- **Username**: `admin`
- **Password**: `changeme`
- **Role**: owner

**⚠️ IMPORTANT**: Change the default password immediately after first login!

```bash
curl -X POST http://localhost:8000/api/auth/change-password \
  -H "Content-Type: application/json" \
  -d '{"current_password": "changeme", "new_password": "YourSecurePassword123!"}'
```

---

## Local Development Setup (Without Docker)

For active development with hot-reloading and debugging.

### Backend Setup

#### 1. Install Python Dependencies

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### 2. Install and Configure PostgreSQL + TimescaleDB

**Option A: Docker (Recommended)**

```bash
docker run -d --name ddms-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=ddms \
  -p 5432:5432 \
  timescale/timescaledb:latest-pg15
```

**Option B: Native Installation**

Ubuntu/Debian:
```bash
sudo apt-get install postgresql-15 postgresql-15-timescaledb-2
sudo systemctl start postgresql
```

macOS (Homebrew):
```bash
brew install postgresql@15 timescaledb
brew services start postgresql@15
```

#### 3. Configure Environment Variables

Create `backend/.env`:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ddms

# Security
SECRET_KEY=your-secret-key-here-min-32-chars  # Generate with: openssl rand -hex 32
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (for development)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Modbus (optional overrides)
MODBUS_TIMEOUT_SECONDS=3
MODBUS_RETRY_INTERVAL_SECONDS=60
```

#### 4. Initialize Database

```bash
cd backend

# Run migrations
alembic upgrade head

# Seed default data (owner account + configuration)
python -m src.db.init_default_data
```

#### 5. Run Backend Server

```bash
# Development mode with hot-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn src.main:app --workers 4 --host 0.0.0.0 --port 8000
```

#### 6. Run Tests (TDD Requirement)

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest tests/contract/      # Contract tests only

# Coverage must be >= 80% (constitution requirement)
```

Coverage report will be in `backend/htmlcov/index.html`.

---

### Frontend Setup

#### 1. Install Node.js Dependencies

```bash
cd frontend
npm install
```

#### 2. Configure Environment Variables

Create `frontend/.env.local`:

```env
# API endpoint
VITE_API_URL=http://localhost:8000/api

# Feature flags (optional)
VITE_ENABLE_DEBUG=true
```

#### 3. Run Development Server

```bash
npm run dev
```

Frontend will be available at http://localhost:5173 (Vite default).

#### 4. Build for Production

```bash
npm run build
npm run preview  # Test production build locally
```

#### 5. Run Tests

```bash
# Unit tests with coverage
npm run test:unit

# E2E tests (requires backend running)
npm run test:e2e

# Coverage report
npm run test:coverage
```

---

## Development Workflow

### Adding a New Feature

1. **Create Feature Branch**

```bash
git checkout -b 002-new-feature
```

2. **Write Tests First (TDD)**

```bash
# Backend
touch backend/tests/unit/test_new_feature.py
# Write failing tests

# Frontend
touch frontend/tests/unit/NewFeature.test.tsx
# Write failing tests
```

3. **Verify Tests Fail**

```bash
pytest tests/unit/test_new_feature.py  # Should fail
npm run test:unit NewFeature.test.tsx  # Should fail
```

4. **Implement Feature**

```bash
# Write minimal code to pass tests
```

5. **Verify Tests Pass**

```bash
pytest --cov=src --cov-report=term  # Coverage must be >= 80%
npm run test:coverage               # Check frontend coverage
```

6. **Run Linters**

```bash
# Backend
black src/ tests/           # Format code
flake8 src/ tests/          # Lint
mypy src/                   # Type check

# Frontend
npm run lint                # ESLint
npm run format              # Prettier
```

7. **Commit and Push**

```bash
git add .
git commit -m "feat: add new feature with tests (>=80% coverage)"
git push origin 002-new-feature
```

### Running Specific Services

```bash
# Backend only
cd backend && uvicorn src.main:app --reload

# Frontend only (requires backend running)
cd frontend && npm run dev

# Database only
docker run -d -p 5432:5432 timescale/timescaledb:latest-pg15

# Background data collector (for testing Modbus)
cd backend && python -m src.collectors.device_manager
```

---

## Simulating Modbus Devices (for Testing)

For development without physical Modbus devices, use a simulator.

### Option 1: pymodbus Simulator

```bash
pip install pymodbus[repl]

# Start simulator
pymodbus.simulator --modbus_server tcp --modbus_port 502
```

Configure device in DDMS:
- IP: `localhost` or `127.0.0.1`
- Port: `502`
- Register: `1-100` (simulator provides default registers)

### Option 2: Docker Modbus Simulator

```bash
docker run -d -p 5020:502 oitc/modbus-server
```

Configure device with port `5020`.

### Option 3: Mock Device (for Unit Tests)

```python
# In tests, use pytest-mock
def test_device_collection(mocker):
    mock_client = mocker.patch('pymodbus.client.tcp.AsyncModbusTcpClient')
    mock_client.return_value.read_holding_registers.return_value.registers = [1234]
    # ... test logic
```

---

## Database Migrations

### Creating a New Migration

```bash
cd backend

# Auto-generate migration from model changes
alembic revision --autogenerate -m "add new column to devices"

# Edit generated file in: backend/src/db/migrations/versions/XXXXX_add_new_column.py
# Verify upgrade() and downgrade() functions

# Apply migration
alembic upgrade head
```

### Rolling Back Migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade abc123

# Rollback all migrations
alembic downgrade base
```

### Checking Migration Status

```bash
alembic current  # Show current version
alembic history  # Show all migrations
alembic show abc123  # Show specific migration details
```

---

## Production Deployment (On-Premises)

### Prerequisites

- Linux server (Ubuntu 20.04+ or RHEL 8+)
- Docker and Docker Compose installed
- SSL/TLS certificate for HTTPS (Let's Encrypt or internal CA)
- Firewall configured (allow ports 443 for HTTPS, 502 for Modbus)

### 1. Prepare Server

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Clone and Configure

```bash
git clone https://github.com/your-org/demo-monitor.git
cd demo-monitor
git checkout 001-ddms-web-application

# Create production environment file
cp .env.example .env.production
nano .env.production
```

**Production `.env.production`**:

```env
# Database
DATABASE_URL=postgresql://ddms_user:STRONG_PASSWORD@postgres:5432/ddms

# Security (CRITICAL: Generate strong random keys)
SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
WORKERS=4

# Frontend
VITE_API_URL=https://ddms.yourcompany.local/api

# TLS/SSL
SSL_CERT_PATH=/etc/ssl/certs/ddms.crt
SSL_KEY_PATH=/etc/ssl/private/ddms.key

# Backup
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"  # 2 AM daily
BACKUP_RETENTION_DAYS=30
```

### 3. Build Docker Images

```bash
docker-compose -f docker-compose.prod.yml build
```

### 4. Start Services

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 5. Initialize Production Database

```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
docker-compose -f docker-compose.prod.yml exec backend python -m src.db.init_default_data
```

### 6. Configure Automated Backups

```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /opt/ddms/scripts/backup.sh
```

**Backup script** (`scripts/backup.sh`):

```bash
#!/bin/bash
BACKUP_DIR="/opt/ddms/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ddms_backup_$TIMESTAMP.sql.gz"

# Create backup
docker-compose -f /opt/ddms/docker-compose.prod.yml exec -T postgres \
  pg_dump -U ddms_user ddms | gzip > "$BACKUP_FILE"

# Keep last 30 days
find "$BACKUP_DIR" -name "ddms_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

### 7. Configure Systemd Service (Optional)

Create `/etc/systemd/system/ddms.service`:

```ini
[Unit]
Description=DDMS Web Application
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/ddms
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
User=ddms

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable ddms
sudo systemctl start ddms
sudo systemctl status ddms
```

### 8. Configure Reverse Proxy (Nginx)

Install Nginx and configure HTTPS:

```nginx
server {
    listen 443 ssl http2;
    server_name ddms.yourcompany.local;

    ssl_certificate /etc/ssl/certs/ddms.crt;
    ssl_certificate_key /etc/ssl/private/ddms.key;
    ssl_protocols TLSv1.3;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # SSE real-time updates
    location /api/devices/stream {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
    }
}
```

---

## Monitoring and Operations

### Health Check

```bash
curl http://localhost:8000/api/system/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "devices_online": 95,
  "devices_total": 100,
  "uptime_seconds": 86400,
  "version": "1.0.0"
}
```

### View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Database Console

```bash
docker-compose exec postgres psql -U ddms_user ddms
```

Useful queries:

```sql
-- Check device count
SELECT COUNT(*) FROM devices;

-- Check reading count
SELECT COUNT(*) FROM readings;

-- Check database size
SELECT pg_size_pretty(pg_database_size('ddms'));

-- Check hypertable status
SELECT * FROM timescaledb_information.hypertables;
```

### Performance Metrics

Access Prometheus metrics:

```bash
curl http://localhost:8000/metrics
```

Example metrics:
- `ddms_device_readings_total` - Total readings collected
- `ddms_device_errors_total` - Device errors by type
- `ddms_api_request_duration_seconds` - API latency histogram

---

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# - Database not ready: wait 10s and retry
# - Port 8000 in use: change BACKEND_PORT in .env
# - Missing SECRET_KEY: generate with openssl rand -hex 32
```

### Frontend Build Fails

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Must be 18+
```

### Device Connection Fails

```bash
# Test Modbus connectivity
telnet <device_ip> 502

# Check device configuration in database
docker-compose exec postgres psql -U ddms_user ddms -c "SELECT * FROM devices WHERE name = 'your_device';"

# View collector logs
docker-compose logs -f backend | grep modbus
```

### Database Performance Issues

```bash
# Check slow queries
docker-compose exec postgres psql -U ddms_user ddms -c "SELECT * FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;"

# Reindex TimescaleDB
docker-compose exec postgres psql -U ddms_user ddms -c "REINDEX DATABASE ddms;"

# Update table statistics
docker-compose exec postgres psql -U ddms_user ddms -c "ANALYZE;"
```

### Test Coverage Below 80%

```bash
# Generate detailed coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Identify untested modules (marked in red)
# Write tests for uncovered lines
```

---

## Next Steps

- **Configure Devices**: Add Modbus devices via UI or API
- **Set Up Users**: Create admin and read-only accounts
- **Configure Groups**: Organize devices by production line/area
- **Set Thresholds**: Define warning/critical limits for each device
- **Test Alerts**: Verify threshold violations trigger visual indicators
- **Export Data**: Test CSV export for reporting
- **Language Switching**: Verify EN/CN translations

---

## Additional Resources

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Constitution**: `.specify/memory/constitution.md` (development principles)
- **Data Model**: `specs/001-ddms-web-application/data-model.md`
- **API Contracts**: `specs/001-ddms-web-application/contracts/openapi.yaml`
- **Architecture Decisions**: `docs/architecture/` (ADRs)

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Verify health: `curl http://localhost:8000/api/system/health`
3. Review documentation in `docs/`
4. Check constitution compliance: `.specify/memory/constitution.md`

**Remember**: All code changes must maintain >= 80% test coverage per constitution Principle III!

