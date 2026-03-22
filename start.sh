#!/bin/bash
set -e

echo "🎵 Starting VIBE — Istanbul Event Discovery"
echo "============================================"

# Backend setup
echo ""
echo "→ Setting up backend..."
cd "$(dirname "$0")/backend"

if ! command -v python3 &>/dev/null; then
  echo "❌ Python 3 not found. Please install Python 3.9+"
  exit 1
fi

# Create virtualenv if needed
if [ ! -d ".venv" ]; then
  echo "  Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate
echo "  Installing Python dependencies..."
pip install -q -r requirements.txt

# Seed initial data
echo "  Seeding initial events..."
python seed.py

# Start backend in background
echo "  Starting FastAPI backend on http://localhost:8000"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"

# Wait for backend to be ready
echo "  Waiting for backend..."
for i in {1..15}; do
  if curl -s http://localhost:8000/scraper/status > /dev/null 2>&1; then
    echo "  ✓ Backend ready"
    break
  fi
  sleep 1
done

# Frontend setup
echo ""
echo "→ Setting up frontend..."
cd "$(dirname "$0")/frontend"

if ! command -v node &>/dev/null; then
  echo "❌ Node.js not found. Please install Node.js 18+"
  exit 1
fi

echo "  Installing frontend dependencies..."
# Use bun if available (much faster), otherwise npm
if command -v bun &>/dev/null || [ -f "$HOME/.bun/bin/bun" ]; then
  BUN="${HOME}/.bun/bin/bun"
  "$BUN" install
elif command -v npm &>/dev/null; then
  npm install
else
  echo "❌ Neither bun nor npm found. Install Node.js 18+ or Bun."
  exit 1
fi

echo "  Starting Vite dev server on http://localhost:5173"
echo ""
echo "============================================"
echo "  ✦ VIBE is running!"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"
echo "  Press Ctrl+C to stop"
echo "============================================"
echo ""

npm run dev

# Cleanup backend on exit
trap "kill $BACKEND_PID 2>/dev/null" EXIT
