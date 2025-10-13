#!/bin/bash
#
# DDMS Application Stop Script
# Stops all running services
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Stopping DDMS services..."

# Stop frontend
if [ -f "$PROJECT_ROOT/logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$PROJECT_ROOT/logs/frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null; then
        kill $FRONTEND_PID
        echo "✓ Frontend server stopped"
    fi
    rm "$PROJECT_ROOT/logs/frontend.pid"
fi

# Stop backend
if [ -f "$PROJECT_ROOT/logs/backend.pid" ]; then
    BACKEND_PID=$(cat "$PROJECT_ROOT/logs/backend.pid")
    if ps -p $BACKEND_PID > /dev/null; then
        kill $BACKEND_PID
        echo "✓ Backend server stopped"
    fi
    rm "$PROJECT_ROOT/logs/backend.pid"
fi

# Stop database
cd "$PROJECT_ROOT"
docker compose down
echo "✓ Database stopped"

echo ""
echo "All services stopped."
