#!/bin/bash
# Start all services for NBA Data project

echo "Starting NBA Data services..."
echo "================================"

# Check if PostgreSQL is running
echo "[1/3] Checking PostgreSQL..."
if pg_isready -q; then
    echo "✓ PostgreSQL is running"
else
    echo "✗ PostgreSQL is not running. Please start PostgreSQL first."
    exit 1
fi

# Start backend
echo "[2/3] Starting backend (FastAPI)..."
cd backend
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..
echo "✓ Backend started (PID: $BACKEND_PID)"

# Start frontend (when implemented)
echo "[3/3] Starting frontend (React)..."
# cd frontend
# npm run dev &
# FRONTEND_PID=$!
# cd ..
echo "⚠ Frontend not yet implemented"

echo "================================"
echo "Services started!"
echo ""
echo "Backend API:  http://localhost:8000"
echo "API Docs:     http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for backend process
wait $BACKEND_PID
