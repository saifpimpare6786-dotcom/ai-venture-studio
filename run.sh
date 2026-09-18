#!/bin/bash
echo "==================================================="
echo "  Apex Venture Studio - Autonomous Launch Script"
echo "==================================================="
echo ""

# Check dependencies
command -v python3 >/dev/null 2>&1 || { echo >&2 "[ERROR] Python 3 is required but not installed."; exit 1; }
command -v npm >/dev/null 2>&1 || { echo >&2 "[ERROR] npm is required but not installed."; exit 1; }

echo "[1/2] Starting FastAPI Backend on http://localhost:8000 ..."
(cd backend && python3 main.py) &
BACKEND_PID=$!

sleep 2

echo "[2/2] Starting Vite Frontend on http://localhost:5173 ..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "==================================================="
echo "  Venture Studio is running!"
echo "  Dashboard: http://localhost:5173"
echo "  API Docs:  http://localhost:8000/docs"
echo "==================================================="
echo "Press Ctrl+C to terminate both servers."

trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait
