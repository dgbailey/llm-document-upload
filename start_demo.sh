#!/bin/bash

echo "🚀 Starting AI Document Summary Demo Mode..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create necessary directories
mkdir -p backend/uploads

# Start Redis if not running (using Redis for demo, fallback to in-memory if not available)
if command -v redis-server &> /dev/null; then
    echo -e "${YELLOW}Starting Redis...${NC}"
    redis-server --daemonize yes 2>/dev/null || true
else
    echo -e "${YELLOW}Redis not found, using in-memory queue${NC}"
fi

# Start backend
echo -e "${BLUE}Starting Backend Server...${NC}"
cd backend
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate

# Initialize database
python3 -c "from app.database import init_db; init_db()" 2>/dev/null || true

# Start FastAPI in background
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start Celery worker in background
celery -A app.celery_app worker --loglevel=info &
CELERY_PID=$!

cd ..

# Install frontend dependencies if needed
echo -e "${BLUE}Starting Frontend...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Wait for backend to be ready
echo -e "${YELLOW}Waiting for backend to be ready...${NC}"
sleep 5

# Start frontend
echo -e "${GREEN}Starting Frontend Server...${NC}"
npm run dev &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}✨ Demo Mode is running!${NC}"
echo ""
echo -e "${BLUE}Access the application at:${NC}"
echo -e "  Frontend: ${GREEN}http://localhost:5173${NC}"
echo -e "  Backend API: ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs: ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}Demo Features:${NC}"
echo "  • No API keys required"
echo "  • Simulated AI processing with random delays"
echo "  • 10% failure rate for testing error handling"
echo "  • 20% slow task simulation"
echo "  • Realistic cost estimation"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $CELERY_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    redis-cli shutdown 2>/dev/null || true
    echo -e "${GREEN}Demo stopped.${NC}"
    exit 0
}

# Set trap to cleanup on Ctrl+C
trap cleanup INT

# Wait for services
wait