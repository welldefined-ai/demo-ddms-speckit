# DDMS Production Deployment Quickstart

**Version**: 1.0
**Last Updated**: 2025-10-16
**Target Audience**: System operators, DevOps engineers
**Estimated Time**: 45-60 minutes

## Overview

This guide provides step-by-step instructions for deploying the Device Data Monitoring System (DDMS) to production on-premises servers. By following this guide, you will deploy a fully functional DDMS instance with HTTPS access, automated backups, and production-ready security configurations.

### What This Guide Covers

- Production server setup and prerequisites
- Docker-based deployment with Nginx reverse proxy
- TLS certificate configuration for HTTPS access
- Automated database backup configuration
- Zero-downtime update procedures
- CI/CD pipeline setup with GitHub Actions
- Monitoring and health check configuration
- Common troubleshooting scenarios

### What This Guide Does NOT Cover

- Development environment setup (see main README.md)
- Modbus device configuration (see device management documentation)
- Application-level configuration (user management, device groups, etc.)

### Prerequisites

Before starting this deployment, ensure you have:

- Clean server running Ubuntu 20.04+ or Debian 11+
- Root or sudo access to the server
- Domain name pointing to your server (for HTTPS)
- TLS certificates (Let's Encrypt or custom CA)
- Basic Linux system administration knowledge
- 60 minutes of uninterrupted time

---

## Server Requirements

### Hardware Specifications

**Minimum Requirements** (up to 100 devices):
- **CPU**: 2 cores (2.0 GHz or higher)
- **RAM**: 4 GB
- **Storage**: 50 GB available disk space
- **Network**: 100 Mbps network interface

**Recommended Requirements** (100-1000 devices):
- **CPU**: 4 cores (2.5 GHz or higher)
- **RAM**: 8 GB
- **Storage**: 100 GB SSD
- **Network**: 1 Gbps network interface

**Storage Breakdown**:
- Docker images: ~2 GB
- PostgreSQL database: ~10-50 GB (depends on retention period and device count)
- Backup storage: ~20-30% of database size
- Application logs: ~5 GB
- Operating system: ~10 GB

### Software Requirements

**Required Software**:
- **Operating System**: Ubuntu 20.04 LTS, Ubuntu 22.04 LTS, Debian 11, or Debian 12
- **Docker**: Version 24.0 or later
- **Docker Compose**: Version 2.0 or later
- **Git**: Version 2.30 or later

**Optional Software**:
- **UFW** (Uncomplicated Firewall) - for firewall management
- **Certbot** - for Let's Encrypt TLS certificates
- **Prometheus** - for external metrics collection (not included in DDMS)

### Network Requirements

**Required Ports**:
- **443/tcp** - HTTPS access (must be open to users)
- **80/tcp** - HTTP redirect to HTTPS (can be closed after setup)

**Internal Ports** (Docker internal, do not expose):
- 5432/tcp - PostgreSQL database
- 8000/tcp - FastAPI backend
- 3000/tcp - Frontend development server (production uses Nginx)

**Network Configuration**:
- Static IP address assigned to server
- DNS A record pointing to server IP address
- No NAT or port forwarding issues between users and server
- Access to internal network for Modbus device communication

**Firewall Note**: If your server is behind a corporate firewall, ensure ports 80 and 443 are allowed from user networks.

---

## Pre-Deployment Checklist

Complete these steps before running the deployment script:

### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required dependencies
sudo apt install -y curl git ufw

# Verify system resources
free -h                    # Check available RAM (minimum 4GB)
df -h                      # Check available disk space (minimum 50GB)
nproc                      # Check CPU cores (minimum 2)
```

### 2. Install Docker and Docker Compose

```bash
# Install Docker (official method)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group (avoids needing sudo)
sudo usermod -aG docker $USER

# Apply group membership (logout/login or run)
newgrp docker

# Install Docker Compose plugin
sudo apt install -y docker-compose-plugin

# Verify installations
docker --version           # Should be 24.0+
docker compose version     # Should be 2.0+
```

### 3. Configure Firewall

```bash
# Install UFW if not already installed
sudo apt install -y ufw

# Allow SSH (important - do this first!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw --force enable

# Verify firewall status
sudo ufw status verbose
```

### 4. Prepare TLS Certificates

Choose one of the following methods:

**Option A: Let's Encrypt (Recommended for internet-facing servers)**

See [TLS Certificate Setup](#tls-certificate-setup) section below for detailed Let's Encrypt instructions.

**Option B: Custom CA (For internal deployments)**

Place your existing certificates in the following locations:
```bash
# Create certificate directory
sudo mkdir -p /opt/ddms/certs

# Copy your certificates
sudo cp /path/to/your/fullchain.pem /opt/ddms/certs/cert.pem
sudo cp /path/to/your/privkey.pem /opt/ddms/certs/key.pem

# Set proper permissions
sudo chmod 600 /opt/ddms/certs/key.pem
sudo chmod 644 /opt/ddms/certs/cert.pem
```

### 5. DNS Configuration

Ensure your domain name resolves to your server:

```bash
# Verify DNS resolution
nslookup ddms.yourdomain.com

# Should return your server's IP address
# If not, update your DNS A record and wait for propagation (up to 24 hours)
```

**Pre-Deployment Verification**:
```bash
# Run all checks before proceeding
echo "Docker: $(docker --version)"
echo "Docker Compose: $(docker compose version)"
echo "Disk Space: $(df -h / | awk 'NR==2 {print $4}')"
echo "RAM: $(free -h | awk 'NR==2 {print $7}')"
echo "Certificates: $(ls -lh /opt/ddms/certs/)"
```

If all checks pass, proceed to deployment.

---

## Production Deployment Steps

### Step 1: Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/ddms
sudo chown $USER:$USER /opt/ddms
cd /opt/ddms

# Clone repository
git clone https://github.com/your-org/ddms.git .

# Checkout production branch (if using feature branch)
git checkout 002-finish-remaining-tasks

# Verify repository structure
ls -la
# Should see: backend/ frontend/ docker/ scripts/ README.md
```

### Step 2: Configure Environment Variables

```bash
# Copy example production environment file
cp backend/.env.example backend/.env.production

# Edit environment variables
nano backend/.env.production
```

**Required Configuration** (update all values marked with `CHANGE_THIS`):

```bash
# Database Configuration
DATABASE_URL=postgresql://ddms_prod:CHANGE_THIS_PASSWORD@db:5432/ddms
POSTGRES_DB=ddms
POSTGRES_USER=ddms_prod
POSTGRES_PASSWORD=CHANGE_THIS_PASSWORD

# JWT Authentication (generate secure random strings)
JWT_SECRET_KEY=CHANGE_THIS_TO_RANDOM_64_CHAR_STRING
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Settings
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO

# CORS Settings (update with your domain)
CORS_ORIGINS=https://ddms.yourdomain.com

# Modbus Configuration
MODBUS_TIMEOUT=10
MODBUS_RETRY_ATTEMPTS=3

# Metrics and Monitoring
PROMETHEUS_ENABLED=True
METRICS_PORT=9090

# Backup Configuration
BACKUP_ENABLED=True
BACKUP_SCHEDULE=0 2 * * *              # Daily at 2 AM
BACKUP_RETENTION_DAYS=30
BACKUP_PATH=/backups

# Security Settings
CSRF_ENABLED=True
RATE_LIMIT_PER_MINUTE=100
SESSION_TIMEOUT_MINUTES=60

# Nginx Settings (update with your domain)
SERVER_NAME=ddms.yourdomain.com
TLS_CERT_PATH=/etc/nginx/ssl/cert.pem
TLS_KEY_PATH=/etc/nginx/ssl/key.pem
```

**Generate Secure Secrets**:

```bash
# Generate JWT secret key (64 characters)
openssl rand -hex 32

# Generate database password (32 characters)
openssl rand -base64 32

# Generate CSRF secret (32 characters)
openssl rand -hex 32
```

**Save and Verify Configuration**:
```bash
# Verify no example values remain
grep -i "CHANGE_THIS" backend/.env.production
# Should return no results

# Set proper file permissions
chmod 600 backend/.env.production
```

### Step 3: Configure Nginx

Update Nginx configuration with your domain name:

```bash
# Edit Nginx configuration
nano docker/nginx.conf
```

Update the `server_name` directive:
```nginx
server {
    listen 443 ssl http2;
    server_name ddms.yourdomain.com;  # <-- Update this line

    # Rest of configuration...
}
```

Verify certificate paths in Nginx configuration:
```nginx
ssl_certificate /etc/nginx/ssl/cert.pem;
ssl_certificate_key /etc/nginx/ssl/key.pem;
```

### Step 4: Run Deployment Script

```bash
# Make deployment script executable
chmod +x scripts/deploy.sh

# Run deployment (this will take 5-10 minutes)
./scripts/deploy.sh

# The script will:
# 1. Validate environment configuration
# 2. Build Docker images (backend, frontend)
# 3. Initialize database schema
# 4. Run database migrations
# 5. Start all services (PostgreSQL, backend, Nginx)
# 6. Wait for health checks to pass
```

**Expected Output**:
```
[INFO] Starting DDMS production deployment...
[INFO] Validating environment configuration... OK
[INFO] Building Docker images...
[INFO] Building backend image... OK (2m 15s)
[INFO] Building frontend image... OK (1m 30s)
[INFO] Starting PostgreSQL database... OK
[INFO] Waiting for database to be ready... OK
[INFO] Running database migrations... OK (3 migrations applied)
[INFO] Starting backend services... OK (2 replicas)
[INFO] Starting Nginx reverse proxy... OK
[INFO] Waiting for health checks to pass...
[INFO] Health check: HEALTHY
[INFO] Deployment completed successfully!
[INFO] DDMS is now accessible at: https://ddms.yourdomain.com
```

**If Deployment Fails**: See [Troubleshooting](#troubleshooting-common-issues) section below.

### Step 5: Verify Health Endpoint

```bash
# Check health endpoint (local)
curl -k https://localhost/api/system/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "database": "connected",
#   "uptime_seconds": 42
# }

# Check health endpoint (remote)
curl https://ddms.yourdomain.com/api/system/health
```

### Step 6: Access Web Interface

1. Open web browser
2. Navigate to `https://ddms.yourdomain.com`
3. Login with default credentials:
   - **Username**: `admin`
   - **Password**: `admin` (CHANGE THIS IMMEDIATELY)

**First Login Steps**:
1. Login with default credentials
2. Navigate to **Settings** > **User Management**
3. Change admin password immediately
4. Create additional user accounts as needed
5. Test device connectivity and dashboard

**Deployment Complete!** Your DDMS instance is now running in production.

---

## TLS Certificate Setup

### Method 1: Let's Encrypt with Certbot (Automated Renewal)

**Prerequisites**:
- Domain name pointing to your server
- Ports 80 and 443 accessible from internet

**Installation**:
```bash
# Install Certbot
sudo apt update
sudo apt install -y certbot

# Stop Nginx (if running) to free port 80
docker compose -f docker/docker-compose.prod.yml stop nginx

# Obtain certificate (replace with your domain and email)
sudo certbot certonly --standalone \
    -d ddms.yourdomain.com \
    --email admin@yourdomain.com \
    --agree-tos \
    --non-interactive

# Certificate files will be at:
# /etc/letsencrypt/live/ddms.yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/ddms.yourdomain.com/privkey.pem
```

**Copy Certificates to DDMS Directory**:
```bash
# Create certificate directory
sudo mkdir -p /opt/ddms/certs

# Copy certificates (create symlinks for auto-renewal)
sudo ln -s /etc/letsencrypt/live/ddms.yourdomain.com/fullchain.pem \
    /opt/ddms/certs/cert.pem
sudo ln -s /etc/letsencrypt/live/ddms.yourdomain.com/privkey.pem \
    /opt/ddms/certs/key.pem

# Set permissions
sudo chmod 755 /opt/ddms/certs
sudo chmod 644 /opt/ddms/certs/cert.pem
sudo chmod 600 /opt/ddms/certs/key.pem
```

**Setup Automated Renewal**:
```bash
# Test renewal process (dry run)
sudo certbot renew --dry-run

# Certbot automatically installs renewal timer
# Verify renewal timer is active
systemctl list-timers | grep certbot

# Create post-renewal hook to reload Nginx
sudo mkdir -p /etc/letsencrypt/renewal-hooks/post
sudo nano /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh
```

Add the following content:
```bash
#!/bin/bash
cd /opt/ddms
docker compose -f docker/docker-compose.prod.yml exec nginx nginx -s reload
```

Make executable:
```bash
sudo chmod +x /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh
```

**Verification**:
```bash
# Check certificate validity
openssl x509 -in /opt/ddms/certs/cert.pem -noout -dates

# Test HTTPS connection
curl -v https://ddms.yourdomain.com 2>&1 | grep "SSL certificate verify"
# Should show "SSL certificate verify ok"
```

### Method 2: Custom CA Certificate (Internal Deployments)

**For organizations with internal Certificate Authority**:

```bash
# Create certificate directory
sudo mkdir -p /opt/ddms/certs

# Copy your certificates
sudo cp /path/to/fullchain.pem /opt/ddms/certs/cert.pem
sudo cp /path/to/privkey.pem /opt/ddms/certs/key.pem

# Set proper permissions
sudo chmod 644 /opt/ddms/certs/cert.pem
sudo chmod 600 /opt/ddms/certs/key.pem
sudo chown root:root /opt/ddms/certs/*

# Verify certificate chain
openssl verify -CAfile /path/to/ca-bundle.crt /opt/ddms/certs/cert.pem
# Should show: OK
```

**Trust Custom CA on Client Browsers**:
- **Windows**: Import CA certificate to Trusted Root Certificate Authorities
- **macOS**: Add CA certificate to Keychain Access > System > Certificates
- **Linux**: Copy CA cert to `/usr/local/share/ca-certificates/` and run `sudo update-ca-certificates`

### Method 3: Self-Signed Certificate (Testing Only)

**WARNING**: Self-signed certificates should ONLY be used for testing, never in production.

```bash
# Generate self-signed certificate (valid for 365 days)
sudo mkdir -p /opt/ddms/certs
sudo openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
    -keyout /opt/ddms/certs/key.pem \
    -out /opt/ddms/certs/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=ddms.yourdomain.com"

# Set permissions
sudo chmod 644 /opt/ddms/certs/cert.pem
sudo chmod 600 /opt/ddms/certs/key.pem
```

**Accessing with Self-Signed Certificate**:
- Browsers will show security warnings
- Click "Advanced" > "Proceed to site" to bypass warning
- NOT suitable for production use

### Nginx TLS Configuration Verification

After installing certificates, verify Nginx TLS configuration:

```bash
# Check Nginx configuration syntax
docker compose -f docker/docker-compose.prod.yml exec nginx nginx -t

# Expected output: "syntax is ok" and "test is successful"

# Test TLS configuration with SSL Labs (for internet-facing servers)
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=ddms.yourdomain.com
# Target grade: A or A+

# Test TLS locally
openssl s_client -connect ddms.yourdomain.com:443 -tls1_3
# Should show TLS 1.3 connection established
```

---

## Environment Variables Reference

### Complete Production Environment Variables

```bash
# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
DATABASE_URL=postgresql://ddms_prod:PASSWORD@db:5432/ddms
# Full PostgreSQL connection string
# Format: postgresql://USER:PASSWORD@HOST:PORT/DATABASE

POSTGRES_DB=ddms
# PostgreSQL database name

POSTGRES_USER=ddms_prod
# PostgreSQL username

POSTGRES_PASSWORD=CHANGE_THIS
# PostgreSQL password (must match DATABASE_URL password)
# Generate with: openssl rand -base64 32

# ============================================================================
# JWT AUTHENTICATION
# ============================================================================
JWT_SECRET_KEY=CHANGE_THIS_64_CHAR_STRING
# Secret key for JWT token signing (minimum 32 characters)
# Generate with: openssl rand -hex 32

JWT_ALGORITHM=HS256
# JWT signing algorithm (HS256 recommended)

ACCESS_TOKEN_EXPIRE_MINUTES=30
# JWT token expiration time (30 minutes default)

# ============================================================================
# APPLICATION SETTINGS
# ============================================================================
ENVIRONMENT=production
# Environment mode (production|development|staging)

DEBUG=False
# Debug mode (False for production, True for development)

LOG_LEVEL=INFO
# Logging level (DEBUG|INFO|WARNING|ERROR|CRITICAL)

# ============================================================================
# CORS SETTINGS
# ============================================================================
CORS_ORIGINS=https://ddms.yourdomain.com
# Comma-separated list of allowed origins
# Example: https://ddms.example.com,https://ddms.backup.example.com

# ============================================================================
# MODBUS CONFIGURATION
# ============================================================================
MODBUS_TIMEOUT=10
# Modbus connection timeout in seconds

MODBUS_RETRY_ATTEMPTS=3
# Number of retry attempts for failed Modbus connections

MODBUS_RECONNECT_INTERVAL=60
# Seconds between reconnection attempts for offline devices

# ============================================================================
# METRICS AND MONITORING
# ============================================================================
PROMETHEUS_ENABLED=True
# Enable Prometheus metrics endpoint

METRICS_PORT=9090
# Internal metrics port (not exposed externally)

METRICS_CACHE_SECONDS=10
# Metrics endpoint cache duration

# ============================================================================
# BACKUP CONFIGURATION
# ============================================================================
BACKUP_ENABLED=True
# Enable automated database backups

BACKUP_SCHEDULE=0 2 * * *
# Cron expression for backup schedule (daily at 2 AM default)
# Format: minute hour day month weekday
# Examples:
#   0 2 * * *     = Daily at 2 AM
#   0 2 * * 0     = Weekly on Sunday at 2 AM
#   0 2 1 * *     = Monthly on 1st at 2 AM

BACKUP_RETENTION_DAYS=30
# Number of days to retain backup files

BACKUP_PATH=/backups
# Backup file storage directory (inside container)

BACKUP_COMPRESSION=True
# Enable backup compression (reduces size by 80-90%)

# ============================================================================
# DATA RETENTION
# ============================================================================
DATA_RETENTION_DAYS=90
# Number of days to retain device readings (90 days default)

RETENTION_CHECK_TIME=02:00
# Time to run daily retention policy check (24-hour format)

COMPRESSION_AGE_DAYS=7
# Compress data older than N days (TimescaleDB compression)

# ============================================================================
# SECURITY SETTINGS
# ============================================================================
CSRF_ENABLED=True
# Enable CSRF protection

CSRF_SECRET_KEY=CHANGE_THIS
# CSRF token secret key
# Generate with: openssl rand -hex 32

RATE_LIMIT_PER_MINUTE=100
# Maximum API requests per minute per IP address

SESSION_TIMEOUT_MINUTES=60
# User session timeout in minutes

ALLOWED_HOSTS=ddms.yourdomain.com
# Comma-separated list of allowed hostnames

# ============================================================================
# NGINX SETTINGS
# ============================================================================
SERVER_NAME=ddms.yourdomain.com
# Domain name for Nginx server_name directive

TLS_CERT_PATH=/etc/nginx/ssl/cert.pem
# TLS certificate file path (inside Nginx container)

TLS_KEY_PATH=/etc/nginx/ssl/key.pem
# TLS private key file path (inside Nginx container)

CLIENT_MAX_BODY_SIZE=10M
# Maximum upload size for API requests

# ============================================================================
# SMTP SETTINGS (Optional - for email notifications)
# ============================================================================
SMTP_ENABLED=False
# Enable email notifications

SMTP_HOST=smtp.gmail.com
# SMTP server hostname

SMTP_PORT=587
# SMTP server port (587 for TLS, 465 for SSL)

SMTP_USER=noreply@yourdomain.com
# SMTP username

SMTP_PASSWORD=CHANGE_THIS
# SMTP password

SMTP_FROM=DDMS <noreply@yourdomain.com>
# Email "From" address

# ============================================================================
# ADVANCED SETTINGS (Usually no need to change)
# ============================================================================
WORKERS=4
# Number of Uvicorn worker processes

WORKER_TIMEOUT=120
# Worker timeout in seconds

MAX_CONNECTIONS=1000
# Maximum database connection pool size

DB_POOL_SIZE=20
# Database connection pool size per worker

DB_MAX_OVERFLOW=10
# Maximum overflow connections beyond pool size
```

### Environment Variable Validation

Validate your environment configuration before deployment:

```bash
# Check for example values that need changing
grep -E "CHANGE_THIS|example.com|admin@localhost" backend/.env.production

# Validate cron expression syntax
# Use: https://crontab.guru/ or install cronie
echo "0 2 * * *" | crontab -

# Verify DATABASE_URL format
echo $DATABASE_URL | grep -E "^postgresql://[^:]+:[^@]+@[^:]+:[0-9]+/[^?]+$"

# Check file permissions
ls -la backend/.env.production
# Should be: -rw------- (600)
```

---

## Database Backup and Restore

### Manual Backup

Trigger an immediate backup using the backup script:

```bash
# Navigate to DDMS directory
cd /opt/ddms

# Run manual backup
./scripts/backup.sh

# Expected output:
# [INFO] Starting manual database backup...
# [INFO] Backup file: /opt/ddms/backups/ddms_backup_20251016_143022.sql.gz
# [INFO] Backup size: 2.3 GB (compressed)
# [INFO] Backup completed in 4m 32s
```

**Backup Script Details**:
```bash
#!/bin/bash
# scripts/backup.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/ddms/backups"
BACKUP_FILE="$BACKUP_DIR/ddms_backup_$TIMESTAMP.sql.gz"

# Create backup directory if not exists
mkdir -p "$BACKUP_DIR"

# Execute pg_dump inside database container
docker compose -f docker/docker-compose.prod.yml exec -T db \
    pg_dump -U ddms_prod -d ddms -F c -Z 6 > "$BACKUP_FILE"

echo "[INFO] Backup completed: $BACKUP_FILE"
echo "[INFO] Backup size: $(du -h "$BACKUP_FILE" | cut -f1)"
```

### Automated Backup Schedule

Automated backups are configured via the `BACKUP_SCHEDULE` environment variable.

**Configure Backup Schedule**:
```bash
# Edit environment file
nano backend/.env.production

# Set backup schedule (cron expression)
BACKUP_SCHEDULE=0 2 * * *    # Daily at 2 AM (default)
```

**Common Backup Schedules**:
- Daily at 2 AM: `0 2 * * *`
- Twice daily (2 AM and 2 PM): `0 2,14 * * *`
- Weekly on Sunday at 2 AM: `0 2 * * 0`
- Every 6 hours: `0 */6 * * *`

**Verify Automated Backups**:
```bash
# Check backup job status
docker compose -f docker/docker-compose.prod.yml logs backend | grep backup

# List backup files
ls -lh /opt/ddms/backups/

# Expected output:
# -rw-r--r-- 1 root root 2.3G Oct 16 02:00 ddms_backup_20251016_020000.sql.gz
# -rw-r--r-- 1 root root 2.4G Oct 17 02:00 ddms_backup_20251017_020000.sql.gz
```

### Backup File Management

**Backup Retention Policy**:
- Automatic cleanup keeps last 30 backups (configurable via `BACKUP_RETENTION_DAYS`)
- Manual backups are not automatically deleted
- Backup compression reduces size by 80-90%

**Backup Storage Calculation**:
```
Database Size: 10 GB
Compressed Backup: ~2 GB (80% compression)
30 Days Retention: ~60 GB total storage
```

**Manual Cleanup**:
```bash
# List backups older than 30 days
find /opt/ddms/backups/ -name "ddms_backup_*.sql.gz" -mtime +30

# Delete backups older than 30 days
find /opt/ddms/backups/ -name "ddms_backup_*.sql.gz" -mtime +30 -delete

# Verify remaining backups
ls -lt /opt/ddms/backups/ | head -10
```

### Restore Procedure

**IMPORTANT**: Restoration will **overwrite** the current database. Always backup current database before restoring.

**Step 1: Backup Current Database**:
```bash
# Create backup of current state
./scripts/backup.sh

# Verify backup completed
ls -lh /opt/ddms/backups/ | head -1
```

**Step 2: Stop Backend Services**:
```bash
# Stop backend to prevent new data writes
docker compose -f docker/docker-compose.prod.yml stop backend

# Verify backend is stopped
docker compose -f docker/docker-compose.prod.yml ps
```

**Step 3: Restore Database**:
```bash
# Run restore script (replace with your backup file)
./scripts/restore.sh /opt/ddms/backups/ddms_backup_20251016_020000.sql.gz

# Expected output:
# [INFO] Starting database restore...
# [INFO] Source backup: ddms_backup_20251016_020000.sql.gz
# [INFO] Dropping existing database...
# [INFO] Creating fresh database...
# [INFO] Restoring data... (this may take 5-10 minutes)
# [INFO] Restore completed successfully
```

**Restore Script Details**:
```bash
#!/bin/bash
# scripts/restore.sh

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "[ERROR] Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "[INFO] Starting database restore from $BACKUP_FILE"

# Drop existing database and recreate
docker compose -f docker/docker-compose.prod.yml exec -T db \
    psql -U ddms_prod -d postgres -c "DROP DATABASE IF EXISTS ddms;"

docker compose -f docker/docker-compose.prod.yml exec -T db \
    psql -U ddms_prod -d postgres -c "CREATE DATABASE ddms;"

# Restore from backup
docker compose -f docker/docker-compose.prod.yml exec -T db \
    pg_restore -U ddms_prod -d ddms -c --if-exists < "$BACKUP_FILE"

echo "[INFO] Restore completed"
```

**Step 4: Restart Services**:
```bash
# Start backend services
docker compose -f docker/docker-compose.prod.yml start backend

# Wait for health checks
sleep 10

# Verify health
curl -k https://localhost/api/system/health
```

**Step 5: Verify Restoration**:
```bash
# Check database connection
docker compose -f docker/docker-compose.prod.yml exec db \
    psql -U ddms_prod -d ddms -c "SELECT COUNT(*) FROM devices;"

# Check application logs
docker compose -f docker/docker-compose.prod.yml logs backend | tail -50

# Test web interface
# Login and verify devices, readings, and dashboard load correctly
```

**Rollback if Restore Fails**:
```bash
# If restore fails, restore the backup you created in Step 1
./scripts/restore.sh /opt/ddms/backups/ddms_backup_$(date +%Y%m%d)_*.sql.gz

# Restart services
docker compose -f docker/docker-compose.prod.yml restart
```

---

## Zero-Downtime Updates

Deploy new versions of DDMS without service interruption using rolling updates.

### Update Procedure

**Step 1: Backup Current Database**:
```bash
cd /opt/ddms

# Create pre-update backup
./scripts/backup.sh

# Verify backup completed
ls -lh /opt/ddms/backups/ | head -1
```

**Step 2: Pull Latest Code**:
```bash
# Fetch latest changes
git fetch origin

# Checkout new version (replace with actual version/branch)
git checkout v1.1.0

# Or update current branch
git pull origin main

# Verify version
git log -1 --oneline
```

**Step 3: Update Environment Variables** (if needed):
```bash
# Check for new environment variables in .env.example
diff backend/.env.example backend/.env.production

# Add any new required variables to .env.production
nano backend/.env.production
```

**Step 4: Run Database Migrations**:
```bash
# Run migrations (non-destructive)
docker compose -f docker/docker-compose.prod.yml exec backend \
    alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade abc123 -> def456
# INFO  [alembic.runtime.migration] Running upgrade def456 -> ghi789
```

**Step 5: Rolling Update**:
```bash
# Rebuild images with new code
docker compose -f docker/docker-compose.prod.yml build

# Rolling update (updates one replica at a time)
docker compose -f docker/docker-compose.prod.yml up -d --no-deps --scale backend=2 backend

# Wait for new containers to be healthy
sleep 30

# Verify health endpoint
curl -k https://localhost/api/system/health
```

**Step 6: Update Frontend and Nginx**:
```bash
# Update frontend (brief downtime for static assets)
docker compose -f docker/docker-compose.prod.yml up -d --no-deps frontend

# Reload Nginx configuration (no downtime)
docker compose -f docker/docker-compose.prod.yml exec nginx nginx -s reload

# Verify Nginx is running
docker compose -f docker/docker-compose.prod.yml ps nginx
```

**Step 7: Verify Update**:
```bash
# Check application version
curl https://ddms.yourdomain.com/api/system/health | jq '.version'

# Check running containers
docker compose -f docker/docker-compose.prod.yml ps

# Check logs for errors
docker compose -f docker/docker-compose.prod.yml logs --tail=100 backend

# Test web interface
# Login and verify all functionality works correctly
```

### Rollback Procedure

If update fails or introduces issues, rollback to previous version:

**Step 1: Rollback Code**:
```bash
cd /opt/ddms

# Find previous version
git log --oneline -10

# Checkout previous version (replace with actual commit hash)
git checkout abc123

# Or checkout previous tag
git checkout v1.0.0
```

**Step 2: Rollback Database** (if migrations were applied):
```bash
# Rollback to previous migration (find revision ID in migration file)
docker compose -f docker/docker-compose.prod.yml exec backend \
    alembic downgrade -1

# Or restore from backup
./scripts/restore.sh /opt/ddms/backups/ddms_backup_TIMESTAMP.sql.gz
```

**Step 3: Rebuild and Restart**:
```bash
# Rebuild with previous code
docker compose -f docker/docker-compose.prod.yml build

# Restart all services
docker compose -f docker/docker-compose.prod.yml up -d

# Verify health
curl https://ddms.yourdomain.com/api/system/health
```

### Update Best Practices

1. **Always backup before updates**: Critical for rollback capability
2. **Test in staging first**: Deploy to staging environment before production
3. **Schedule during maintenance window**: Update during low-usage periods
4. **Monitor for 24 hours post-update**: Watch logs and metrics for issues
5. **Keep rollback plan ready**: Document rollback steps before updating
6. **Communicate with users**: Notify users of planned maintenance window

---

## CI Pipeline Setup

Configure automated testing and continuous integration using GitHub Actions.

### Prerequisites

- Repository hosted on GitHub
- GitHub Actions enabled (default for all repositories)
- Repository secrets configured

### Configure Repository Secrets

Navigate to your GitHub repository settings:

**Settings** > **Secrets and variables** > **Actions** > **New repository secret**

Add the following secrets:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `CODECOV_TOKEN` | Codecov upload token (optional) | `abc123...` |
| `DOCKER_USERNAME` | Docker Hub username (if pushing images) | `myorg` |
| `DOCKER_PASSWORD` | Docker Hub password/token | `********` |
| `SLACK_WEBHOOK_URL` | Slack webhook for notifications (optional) | `https://hooks.slack.com/...` |

### Create CI Workflow

The CI workflow file should be at `.github/workflows/ci.yml`:

```bash
# Verify workflow file exists
ls -la .github/workflows/ci.yml

# If not exists, it will be created in feature 002 implementation
```

**Workflow Summary**:
- Runs on every push to `main` and `develop` branches
- Runs on all pull requests to `main`
- Executes backend tests with pytest (Python 3.11, 3.12)
- Executes frontend tests with Vitest (Node 18, 20)
- Enforces 80% test coverage threshold
- Runs linters (black, flake8, mypy, ESLint, Prettier)
- Validates OpenAPI specification
- Builds Docker images (on main branch only)
- Uploads coverage reports to Codecov

### Enable Branch Protection

**Settings** > **Branches** > **Branch protection rules** > **Add rule**

Configure protection for `main` branch:

- [x] Require pull request reviews before merging
- [x] Require status checks to pass before merging
  - Required checks:
    - `backend-tests`
    - `frontend-tests`
    - `contract-tests`
- [x] Require branches to be up to date before merging
- [x] Do not allow bypassing the above settings

**Save Changes**

### Verify CI Pipeline

**Trigger CI Pipeline**:
```bash
# Make a small change
echo "# CI Test" >> README.md

# Commit and push
git add README.md
git commit -m "test: trigger CI pipeline"
git push origin develop
```

**Monitor Pipeline Execution**:
1. Navigate to **Actions** tab in GitHub repository
2. Click on most recent workflow run
3. Monitor job progress (should complete in <10 minutes)
4. Verify all jobs pass successfully

**Expected Jobs**:
- `backend-tests` (Python 3.11)
- `backend-tests` (Python 3.12)
- `frontend-tests` (Node 18)
- `frontend-tests` (Node 20)
- `contract-tests`
- `docker-build` (if pushing to main)

### Coverage Enforcement

**Coverage Threshold**: 80% minimum for both backend and frontend

**Check Coverage Locally**:
```bash
# Backend coverage
cd backend
pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Frontend coverage
cd frontend
npm run test:coverage
```

**Coverage Report in CI**:
- Coverage reports uploaded to Codecov (if token configured)
- View coverage trends at: `https://codecov.io/gh/your-org/ddms`
- Pull requests show coverage diff in comments

### CI Build Status Badge

Add build status badge to README.md:

```markdown
[![CI Pipeline](https://github.com/your-org/ddms/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/ddms/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/your-org/ddms/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/ddms)
```

### CI Pipeline Troubleshooting

**Pipeline Fails on Coverage Check**:
```bash
# Run coverage locally to identify missing tests
pytest --cov=src --cov-report=html
# Open htmlcov/index.html to see coverage details
```

**Docker Build Fails in CI**:
```bash
# Test Docker build locally
docker compose -f docker/docker-compose.prod.yml build

# Check Dockerfile syntax
docker run --rm -i hadolint/hadolint < docker/backend.Dockerfile
```

**Linting Failures**:
```bash
# Run linters locally before pushing
black backend/src backend/tests --check
flake8 backend/src backend/tests
mypy backend/src

cd frontend
npm run lint
npm run format:check
```

---

## Monitoring and Health Checks

### Health Endpoint

DDMS provides a health check endpoint for monitoring system status.

**Health Check URL**: `GET https://ddms.yourdomain.com/api/system/health`

**Response Format**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-16T14:30:22Z",
  "database": {
    "status": "connected",
    "response_time_ms": 12
  },
  "backend": {
    "uptime_seconds": 86400,
    "worker_count": 4
  },
  "devices": {
    "total": 45,
    "connected": 42,
    "offline": 3
  }
}
```

**Health Status Values**:
- `healthy` - All systems operational
- `degraded` - Some non-critical issues (e.g., few devices offline)
- `unhealthy` - Critical issues (e.g., database unreachable)

**Monitoring Integration**:
```bash
# Basic uptime monitoring (cron every 5 minutes)
*/5 * * * * curl -f https://ddms.yourdomain.com/api/system/health || echo "DDMS health check failed" | mail -s "DDMS Alert" admin@yourdomain.com

# UptimeRobot integration
# Add HTTP(s) monitor: https://ddms.yourdomain.com/api/system/health
# Check interval: 5 minutes
# Expected status code: 200

# Nagios/Icinga check
/usr/lib/nagios/plugins/check_http -H ddms.yourdomain.com -u /api/system/health -s "healthy" -S
```

### Prometheus Metrics Endpoint

DDMS exposes Prometheus-compatible metrics for detailed monitoring.

**Metrics URL**: `GET https://ddms.yourdomain.com/metrics`

**No Authentication Required**: Metrics endpoint is public (industry standard for Prometheus)

**Exposed Metrics**:

```prometheus
# Device metrics
ddms_device_readings_total{device_name="Device1",status="success"} 123456
ddms_device_readings_total{device_name="Device1",status="failed"} 45
ddms_active_devices 42
ddms_offline_devices 3

# API metrics
ddms_api_requests_total{method="GET",endpoint="/api/devices",status="200"} 45678
ddms_api_request_duration_seconds_bucket{endpoint="/api/devices",le="0.1"} 42000
ddms_api_request_duration_seconds_bucket{endpoint="/api/devices",le="0.5"} 45000
ddms_api_request_duration_seconds_sum{endpoint="/api/devices"} 5678.90
ddms_api_request_duration_seconds_count{endpoint="/api/devices"} 45678

# Error metrics
ddms_api_errors_total{error_type="ValidationError",endpoint="/api/devices"} 12
ddms_device_errors_total{device_name="Device1",error_type="timeout"} 5

# Database metrics
ddms_database_query_duration_seconds_bucket{query_type="select",le="0.01"} 12000
ddms_database_query_duration_seconds_sum{query_type="select"} 145.67
ddms_database_connections_active 15
ddms_database_connections_max 20

# SSE metrics
ddms_active_sse_connections 8
ddms_sse_messages_sent_total 234567
```

**Test Metrics Endpoint**:
```bash
# Fetch raw metrics
curl https://ddms.yourdomain.com/metrics

# Check specific metric
curl -s https://ddms.yourdomain.com/metrics | grep ddms_active_devices
```

### Setting Up External Prometheus Scraper

**Install Prometheus** (optional, on separate monitoring server):

```bash
# Download Prometheus (on monitoring server)
wget https://github.com/prometheus/prometheus/releases/download/v2.47.0/prometheus-2.47.0.linux-amd64.tar.gz
tar xvfz prometheus-2.47.0.linux-amd64.tar.gz
cd prometheus-2.47.0.linux-amd64

# Create Prometheus configuration
nano prometheus.yml
```

**Prometheus Configuration**:
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ddms'
    scrape_interval: 30s
    static_configs:
      - targets: ['ddms.yourdomain.com:443']
    scheme: https
    metrics_path: /metrics

    # Optional: Basic auth if you add authentication to metrics endpoint
    # basic_auth:
    #   username: prometheus
    #   password: CHANGE_THIS
```

**Start Prometheus**:
```bash
./prometheus --config.file=prometheus.yml

# Access Prometheus UI at: http://monitoring-server:9090
```

**Sample Prometheus Queries**:
```promql
# Average API response time (last 5 minutes)
rate(ddms_api_request_duration_seconds_sum[5m]) / rate(ddms_api_request_duration_seconds_count[5m])

# Error rate (last hour)
sum(rate(ddms_api_errors_total[1h])) by (error_type)

# Device availability percentage
(ddms_active_devices / (ddms_active_devices + ddms_offline_devices)) * 100

# 95th percentile API latency
histogram_quantile(0.95, rate(ddms_api_request_duration_seconds_bucket[5m]))
```

### Log Access

**View Application Logs**:
```bash
cd /opt/ddms

# View all logs
docker compose -f docker/docker-compose.prod.yml logs

# View backend logs only
docker compose -f docker/docker-compose.prod.yml logs backend

# Follow logs in real-time
docker compose -f docker/docker-compose.prod.yml logs -f backend

# View last 100 lines
docker compose -f docker/docker-compose.prod.yml logs --tail=100 backend

# View logs from last hour
docker compose -f docker/docker-compose.prod.yml logs --since=1h backend

# Search logs for errors
docker compose -f docker/docker-compose.prod.yml logs backend | grep ERROR
```

**Log Levels**:
- `DEBUG` - Detailed diagnostic information
- `INFO` - General operational information
- `WARNING` - Warning messages (non-critical issues)
- `ERROR` - Error messages (requires attention)
- `CRITICAL` - Critical errors (system failure)

**Configure Log Level**:
```bash
# Edit environment file
nano backend/.env.production

# Set log level
LOG_LEVEL=INFO  # or DEBUG, WARNING, ERROR

# Restart services to apply
docker compose -f docker/docker-compose.prod.yml restart backend
```

**Log Rotation** (prevent disk space issues):
```bash
# Configure Docker log rotation
sudo nano /etc/docker/daemon.json
```

Add log rotation configuration:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "10"
  }
}
```

Restart Docker daemon:
```bash
sudo systemctl restart docker
```

---

## Troubleshooting Common Issues

### Issue 1: Database Migration Failures

**Symptoms**:
- Deployment fails with "Migration error"
- Backend logs show Alembic errors
- Database schema mismatch

**Diagnosis**:
```bash
# Check migration status
docker compose -f docker/docker-compose.prod.yml exec backend \
    alembic current

# Check pending migrations
docker compose -f docker/docker-compose.prod.yml exec backend \
    alembic heads

# View migration history
docker compose -f docker/docker-compose.prod.yml exec backend \
    alembic history
```

**Solution**:
```bash
# Option 1: Run migrations manually
docker compose -f docker/docker-compose.prod.yml exec backend \
    alembic upgrade head

# Option 2: Rollback and retry
docker compose -f docker/docker-compose.prod.yml exec backend \
    alembic downgrade -1

docker compose -f docker/docker-compose.prod.yml exec backend \
    alembic upgrade head

# Option 3: Restore from backup if corrupted
./scripts/restore.sh /opt/ddms/backups/ddms_backup_LATEST.sql.gz
```

### Issue 2: Nginx Not Starting

**Symptoms**:
- HTTPS access fails
- Port 443 connection refused
- Nginx container exits immediately

**Diagnosis**:
```bash
# Check Nginx container status
docker compose -f docker/docker-compose.prod.yml ps nginx

# View Nginx logs
docker compose -f docker/docker-compose.prod.yml logs nginx

# Test Nginx configuration
docker compose -f docker/docker-compose.prod.yml exec nginx nginx -t
```

**Common Causes and Solutions**:

**A. Port Already in Use**:
```bash
# Check what's using port 443
sudo lsof -i :443

# Stop conflicting service
sudo systemctl stop apache2  # or other web server

# Restart Nginx
docker compose -f docker/docker-compose.prod.yml restart nginx
```

**B. TLS Certificate Issues**:
```bash
# Verify certificate files exist
ls -la /opt/ddms/certs/

# Check certificate validity
openssl x509 -in /opt/ddms/certs/cert.pem -noout -dates

# Check private key
openssl rsa -in /opt/ddms/certs/key.pem -check

# Verify certificate matches key
openssl x509 -noout -modulus -in /opt/ddms/certs/cert.pem | openssl md5
openssl rsa -noout -modulus -in /opt/ddms/certs/key.pem | openssl md5
# Both MD5 hashes should match
```

**C. Configuration Syntax Error**:
```bash
# Validate Nginx configuration syntax
docker compose -f docker/docker-compose.prod.yml exec nginx nginx -t

# If syntax error, review nginx.conf
nano docker/nginx.conf

# Fix errors and restart
docker compose -f docker/docker-compose.prod.yml restart nginx
```

### Issue 3: SSE Connections Not Working Through Proxy

**Symptoms**:
- Dashboard doesn't update in real-time
- Browser console shows EventSource errors
- SSE connection closes immediately

**Diagnosis**:
```bash
# Check Nginx SSE configuration
docker compose -f docker/docker-compose.prod.yml exec nginx cat /etc/nginx/conf.d/default.conf | grep -A 10 "location /api/devices/stream"

# Test SSE endpoint directly (bypass Nginx)
curl -N http://localhost:8000/api/devices/stream

# Test SSE through Nginx
curl -N https://ddms.yourdomain.com/api/devices/stream
```

**Solution**:

Verify Nginx SSE configuration includes:
```nginx
location /api/devices/stream {
    proxy_pass http://fastapi_backend;

    # Critical SSE settings
    proxy_http_version 1.1;
    proxy_buffering off;
    proxy_cache off;
    chunked_transfer_encoding off;

    proxy_set_header Connection '';
    proxy_read_timeout 300s;
}
```

Apply configuration:
```bash
# Reload Nginx
docker compose -f docker/docker-compose.prod.yml exec nginx nginx -s reload

# Or restart Nginx
docker compose -f docker/docker-compose.prod.yml restart nginx
```

### Issue 4: Backup Failures

**Symptoms**:
- Backup script exits with error
- Backup files not created
- Backup notification shows "failed" status

**Diagnosis**:
```bash
# Check backup directory permissions
ls -la /opt/ddms/backups/

# Check disk space
df -h /opt/ddms/backups/

# Check database connectivity
docker compose -f docker/docker-compose.prod.yml exec db psql -U ddms_prod -d ddms -c "SELECT 1;"

# View backup logs
docker compose -f docker/docker-compose.prod.yml logs backend | grep backup
```

**Common Causes and Solutions**:

**A. Insufficient Disk Space**:
```bash
# Check available space
df -h

# Free up space by cleaning old backups
find /opt/ddms/backups/ -name "*.sql.gz" -mtime +30 -delete

# Clean Docker unused volumes
docker system prune -a --volumes
```

**B. Database Connection Issues**:
```bash
# Test database connection
docker compose -f docker/docker-compose.prod.yml exec db psql -U ddms_prod -d ddms -c "SELECT version();"

# Restart database if needed
docker compose -f docker/docker-compose.prod.yml restart db
```

**C. Permission Issues**:
```bash
# Fix backup directory permissions
sudo chown -R $USER:$USER /opt/ddms/backups/
sudo chmod 755 /opt/ddms/backups/

# Make backup script executable
chmod +x scripts/backup.sh
```

### Issue 5: High Disk Usage

**Symptoms**:
- Disk space warning
- System becomes slow
- Backup failures due to insufficient space

**Diagnosis**:
```bash
# Check disk usage by directory
du -sh /opt/ddms/*
du -sh /var/lib/docker/*

# Check database size
docker compose -f docker/docker-compose.prod.yml exec db \
    psql -U ddms_prod -d ddms -c "SELECT pg_size_pretty(pg_database_size('ddms'));"

# Check backup directory size
du -sh /opt/ddms/backups/
```

**Solutions**:

**A. Enable Database Compression** (if not already enabled):
```bash
# Check if compression is enabled
docker compose -f docker/docker-compose.prod.yml exec db \
    psql -U ddms_prod -d ddms -c "SELECT * FROM timescaledb_information.compression_settings;"

# Enable compression (should be automatic in feature 002)
docker compose -f docker/docker-compose.prod.yml exec backend \
    python -c "from src.services.database_service import enable_compression; enable_compression()"
```

**B. Clean Old Backups**:
```bash
# Remove backups older than 30 days
find /opt/ddms/backups/ -name "*.sql.gz" -mtime +30 -delete

# Keep only last 10 backups
ls -t /opt/ddms/backups/*.sql.gz | tail -n +11 | xargs rm -f
```

**C. Clean Docker Resources**:
```bash
# Remove unused Docker images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove all unused resources
docker system prune -a --volumes
```

**D. Adjust Data Retention**:
```bash
# Edit retention period (reduce from 90 to 30 days if needed)
nano backend/.env.production

# Set shorter retention
DATA_RETENTION_DAYS=30

# Restart backend to apply
docker compose -f docker/docker-compose.prod.yml restart backend

# Manually trigger retention cleanup
docker compose -f docker/docker-compose.prod.yml exec backend \
    python -c "from src.services.retention_service import cleanup_old_data; cleanup_old_data()"
```

### Issue 6: Cannot Access Web Interface

**Symptoms**:
- Browser shows "Connection refused"
- SSL certificate warnings
- 502 Bad Gateway errors

**Diagnosis**:
```bash
# Check all services are running
docker compose -f docker/docker-compose.prod.yml ps

# Check health endpoint
curl -k https://localhost/api/system/health

# Test DNS resolution
nslookup ddms.yourdomain.com

# Check firewall
sudo ufw status
```

**Solutions**:

**A. Services Not Running**:
```bash
# Start all services
docker compose -f docker/docker-compose.prod.yml up -d

# Verify all containers running
docker compose -f docker/docker-compose.prod.yml ps
```

**B. Firewall Blocking Access**:
```bash
# Allow HTTPS traffic
sudo ufw allow 443/tcp
sudo ufw allow 80/tcp

# Reload firewall
sudo ufw reload

# Verify rules
sudo ufw status verbose
```

**C. DNS Not Resolving**:
```bash
# Add entry to /etc/hosts temporarily
echo "YOUR_SERVER_IP ddms.yourdomain.com" | sudo tee -a /etc/hosts

# Or update DNS A record at your DNS provider
```

**D. SSL Certificate Issues**:
```bash
# Regenerate Let's Encrypt certificate
sudo certbot renew --force-renewal

# Or generate new self-signed certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
    -keyout /opt/ddms/certs/key.pem \
    -out /opt/ddms/certs/cert.pem

# Restart Nginx
docker compose -f docker/docker-compose.prod.yml restart nginx
```

### Getting Additional Help

If you encounter issues not covered here:

1. **Check Logs**: Always start by checking logs for error messages
   ```bash
   docker compose -f docker/docker-compose.prod.yml logs --tail=200
   ```

2. **Search Documentation**: Review main README.md and API documentation

3. **GitHub Issues**: Search existing issues or create new one at:
   `https://github.com/your-org/ddms/issues`

4. **Contact Support**: Email support team at `support@yourdomain.com`

---

## Security Best Practices

### Firewall Configuration

**Recommended UFW Rules**:
```bash
# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (adjust port if using non-standard)
sudo ufw allow 22/tcp

# Allow HTTPS
sudo ufw allow 443/tcp

# Allow HTTP (for Let's Encrypt and redirect)
sudo ufw allow 80/tcp

# Enable firewall
sudo ufw enable

# Verify configuration
sudo ufw status numbered
```

**Advanced Firewall Rules** (optional):
```bash
# Limit SSH connection attempts (prevent brute force)
sudo ufw limit 22/tcp

# Allow HTTPS from specific IP range only
sudo ufw delete allow 443/tcp
sudo ufw allow from 192.168.1.0/24 to any port 443 proto tcp

# Block specific IP
sudo ufw deny from 203.0.113.0/24
```

### Regular Security Updates

**Enable Automatic Security Updates**:
```bash
# Install unattended-upgrades
sudo apt install -y unattended-upgrades

# Configure automatic updates
sudo dpkg-reconfigure -plow unattended-upgrades

# Verify configuration
cat /etc/apt/apt.conf.d/50unattended-upgrades
```

**Manual Update Schedule**:
```bash
# Weekly system updates (run on Sunday at 2 AM)
0 2 * * 0 apt update && apt upgrade -y && systemctl reboot
```

### Credential Rotation

**Rotate Database Password**:
```bash
# 1. Generate new password
NEW_PASSWORD=$(openssl rand -base64 32)

# 2. Update PostgreSQL password
docker compose -f docker/docker-compose.prod.yml exec db \
    psql -U ddms_prod -d postgres -c "ALTER USER ddms_prod WITH PASSWORD '$NEW_PASSWORD';"

# 3. Update environment file
nano backend/.env.production
# Update POSTGRES_PASSWORD and DATABASE_URL with new password

# 4. Restart backend services
docker compose -f docker/docker-compose.prod.yml restart backend
```

**Rotate JWT Secret**:
```bash
# 1. Generate new JWT secret
NEW_SECRET=$(openssl rand -hex 32)

# 2. Update environment file
nano backend/.env.production
# Update JWT_SECRET_KEY with new secret

# 3. Restart backend (all users will need to re-login)
docker compose -f docker/docker-compose.prod.yml restart backend

# 4. Notify users to re-login
```

**Password Rotation Schedule**:
- Database password: Every 90 days
- JWT secret: Every 180 days
- TLS certificates: Automatically renewed (Let's Encrypt) or manually every 365 days
- User passwords: Enforce 90-day expiration via application settings

### Audit Log Review

**Enable Audit Logging** (if not already enabled):
```bash
# Edit environment file
nano backend/.env.production

# Add audit logging settings
AUDIT_LOG_ENABLED=True
AUDIT_LOG_RETENTION_DAYS=365
```

**Review Audit Logs**:
```bash
# View recent authentication events
docker compose -f docker/docker-compose.prod.yml logs backend | grep "AUTH"

# View configuration changes
docker compose -f docker/docker-compose.prod.yml logs backend | grep "CONFIG_CHANGE"

# View device modifications
docker compose -f docker/docker-compose.prod.yml logs backend | grep "DEVICE_UPDATE"

# Export audit logs for compliance
docker compose -f docker/docker-compose.prod.yml logs backend | grep "AUDIT" > audit_$(date +%Y%m).log
```

**Audit Log Retention**:
```bash
# Keep audit logs for 1 year minimum (compliance requirement)
# Configure log rotation to preserve old logs

sudo nano /etc/logrotate.d/ddms
```

Add configuration:
```
/opt/ddms/logs/*.log {
    daily
    rotate 365
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
}
```

### SSH Hardening

**Recommended SSH Configuration**:
```bash
# Edit SSH configuration
sudo nano /etc/ssh/sshd_config
```

Apply these settings:
```
# Disable root login
PermitRootLogin no

# Use key-based authentication only
PasswordAuthentication no
PubkeyAuthentication yes

# Disable empty passwords
PermitEmptyPasswords no

# Limit authentication attempts
MaxAuthTries 3

# Set idle timeout
ClientAliveInterval 300
ClientAliveCountMax 2

# Allow specific users only
AllowUsers ddms_admin operator1 operator2
```

Restart SSH:
```bash
sudo systemctl restart sshd
```

### Database Security

**PostgreSQL Security Hardening**:
```bash
# Update PostgreSQL configuration
docker compose -f docker/docker-compose.prod.yml exec db \
    psql -U postgres -c "ALTER SYSTEM SET password_encryption = 'scram-sha-256';"

# Require SSL connections
docker compose -f docker/docker-compose.prod.yml exec db \
    psql -U postgres -c "ALTER SYSTEM SET ssl = 'on';"

# Restart database
docker compose -f docker/docker-compose.prod.yml restart db
```

### Security Scanning

**Run Security Scans** (weekly):
```bash
# Install security scanning tools
sudo apt install -y lynis clamav

# Run Lynis security audit
sudo lynis audit system

# Scan for vulnerabilities in Docker images
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image ddms-backend:latest

# Review scan results and address high/critical issues
```

### Backup Encryption

**Encrypt Backup Files** (optional but recommended):
```bash
# Install encryption tools
sudo apt install -y gpg

# Generate GPG key for backups
gpg --gen-key

# Encrypt backup file
gpg --encrypt --recipient backup@yourdomain.com \
    /opt/ddms/backups/ddms_backup_20251016_020000.sql.gz

# Decrypt when needed
gpg --decrypt ddms_backup_20251016_020000.sql.gz.gpg > ddms_backup_20251016_020000.sql.gz
```

**Automated Encryption** (modify backup script):
```bash
# Edit backup script
nano scripts/backup.sh

# Add encryption step after pg_dump
gpg --encrypt --recipient backup@yourdomain.com "$BACKUP_FILE"
rm "$BACKUP_FILE"  # Remove unencrypted version
```

---

## Deployment Checklist Summary

Use this checklist to verify successful production deployment:

### Pre-Deployment
- [ ] Server meets hardware requirements (4GB RAM, 50GB storage, 2+ CPU cores)
- [ ] Ubuntu 20.04+ or Debian 11+ installed
- [ ] Docker 24+ and Docker Compose 2.x installed
- [ ] Domain name configured and DNS resolving
- [ ] TLS certificates obtained and placed in `/opt/ddms/certs/`
- [ ] Firewall configured (ports 80, 443 open)
- [ ] Git repository cloned to `/opt/ddms/`

### Configuration
- [ ] `.env.production` file created and all variables updated
- [ ] No example values remaining (CHANGE_THIS, example.com, etc.)
- [ ] Secure passwords generated for database and JWT
- [ ] Nginx configuration updated with domain name
- [ ] TLS certificate paths verified in Nginx config

### Deployment
- [ ] Deployment script executed successfully
- [ ] All Docker containers running (`docker compose ps`)
- [ ] Health endpoint responding (`/api/system/health`)
- [ ] Web interface accessible via HTTPS
- [ ] Default admin password changed immediately
- [ ] Test user accounts created

### Post-Deployment
- [ ] Automated backups configured and verified
- [ ] First backup completed successfully
- [ ] Retention policy configured (default 90 days)
- [ ] CI pipeline setup and passing
- [ ] Monitoring configured (health checks, Prometheus)
- [ ] Firewall rules verified
- [ ] TLS certificate auto-renewal configured (Let's Encrypt)
- [ ] Security updates enabled
- [ ] Documentation reviewed by operations team

### 30-Day Follow-up
- [ ] System uptime >= 99.9%
- [ ] Daily backups completing successfully
- [ ] No critical errors in logs
- [ ] Performance metrics within acceptable ranges
- [ ] User feedback collected and addressed
- [ ] Security scan completed with no high/critical issues

---

## Appendix: Quick Reference

### Essential Commands

```bash
# Start services
docker compose -f docker/docker-compose.prod.yml up -d

# Stop services
docker compose -f docker/docker-compose.prod.yml down

# Restart services
docker compose -f docker/docker-compose.prod.yml restart

# View logs
docker compose -f docker/docker-compose.prod.yml logs -f

# Check service status
docker compose -f docker/docker-compose.prod.yml ps

# Run backup
./scripts/backup.sh

# Restore from backup
./scripts/restore.sh /path/to/backup.sql.gz

# Check health
curl https://ddms.yourdomain.com/api/system/health

# Update system
git pull && docker compose -f docker/docker-compose.prod.yml build && docker compose -f docker/docker-compose.prod.yml up -d
```

### Important File Locations

| File | Location |
|------|----------|
| Application directory | `/opt/ddms/` |
| Environment config | `/opt/ddms/backend/.env.production` |
| Docker Compose config | `/opt/ddms/docker/docker-compose.prod.yml` |
| Nginx configuration | `/opt/ddms/docker/nginx.conf` |
| TLS certificates | `/opt/ddms/certs/` |
| Database backups | `/opt/ddms/backups/` |
| Application logs | `docker logs ddms-backend` |
| Deployment scripts | `/opt/ddms/scripts/` |

### Support Resources

- **Documentation**: `/opt/ddms/README.md`
- **API Reference**: `/opt/ddms/docs/api/`
- **Architecture Docs**: `/opt/ddms/docs/architecture/`
- **Troubleshooting**: `/opt/ddms/docs/troubleshooting.md`
- **GitHub Issues**: `https://github.com/your-org/ddms/issues`
- **Support Email**: `support@yourdomain.com`

---

**Deployment Guide Version**: 1.0
**Last Updated**: 2025-10-16
**Next Review Date**: 2026-01-16

**Feedback**: If you encounter any issues with this guide or have suggestions for improvement, please submit an issue at the GitHub repository or contact the documentation team.
