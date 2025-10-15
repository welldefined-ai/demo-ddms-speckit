#!/bin/bash
#
# DDMS Application Startup Script
# Initializes database, installs dependencies, and starts all services
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "DDMS - Device Data Monitoring System"
echo "Startup Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Step 1: Start database
echo "Step 1: Starting TimescaleDB..."
cd "$PROJECT_ROOT"
docker compose up -d db
if [ $? -eq 0 ]; then
    print_status "Database container started"
else
    print_error "Failed to start database"
    exit 1
fi

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 5

# Step 2: Install backend dependencies
echo ""
echo "Step 2: Installing backend dependencies..."
cd "$PROJECT_ROOT/backend"
if python3 -m pip install -q -r requirements.txt 2>&1 | grep -q "Successfully installed"; then
    print_status "Backend dependencies installed"
else
    print_warning "Some dependencies may have failed (psycopg2), trying psycopg2-binary..."
    python3 -m pip install -q psycopg2-binary
fi

# Step 3: Run database migrations
echo ""
echo "Step 3: Running database migrations..."
export DATABASE_URL="postgresql://ddms_user:ddms_password@localhost:5432/ddms"
if alembic upgrade head 2>&1 | grep -q "Running upgrade"; then
    print_status "Database migrations completed"
else
    print_warning "Migrations may have already been applied"
fi

# Step 4: Seed default data
echo ""
echo "Step 4: Creating default owner account..."
if python3 src/db/init_default_data.py 2>&1 | grep -q "initialization complete"; then
    print_status "Default data created"
    print_warning "Default credentials: admin / admin123 (CHANGE THIS!)"
else
    print_warning "Default data may already exist"
fi

# Step 5: Start backend server in background
echo ""
echo "Step 5: Starting backend server..."
export DATABASE_URL="postgresql://ddms_user:ddms_password@localhost:5432/ddms"
nohup uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid
sleep 3

if ps -p $BACKEND_PID > /dev/null; then
    print_status "Backend server started (PID: $BACKEND_PID)"
    print_status "Backend running at: http://localhost:8000"
else
    print_error "Backend server failed to start"
    cat ../logs/backend.log
    exit 1
fi

# Step 6: Start frontend dev server in background
echo ""
echo "Step 6: Starting frontend dev server..."
cd "$PROJECT_ROOT/frontend"
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
sleep 5

if ps -p $FRONTEND_PID > /dev/null; then
    print_status "Frontend server started (PID: $FRONTEND_PID)"
    print_status "Frontend running at: http://localhost:3000"
else
    print_error "Frontend server failed to start"
    cat ../logs/frontend.log
    exit 1
fi

# Summary
echo ""
echo "=========================================="
echo "✓ DDMS Application Started Successfully!"
echo "=========================================="
echo ""
echo "Services running:"
echo "  - Database:  localhost:5432"
echo "  - Backend:   http://localhost:8000"
echo "  - Frontend:  http://localhost:3000"
echo ""
echo "Default credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo "Prometheus Metrics: http://localhost:8000/metrics"
echo ""
echo "To stop all services, run:"
echo "  ./scripts/stop.sh"
echo ""
echo "Logs are available in:"
echo "  - Backend:  logs/backend.log"
echo "  - Frontend: logs/frontend.log"
echo ""
print_warning "Note: Dashboard will be empty until devices are configured (User Story 2)"
echo "=========================================="
