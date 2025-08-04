#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}     🚀 AI Document Summary - Complete Demo Setup${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
port_in_use() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

# Kill existing processes
echo -e "${YELLOW}🔧 Cleaning up existing processes...${NC}"
pkill -f "redis-server" 2>/dev/null
pkill -f "uvicorn" 2>/dev/null
pkill -f "celery.*worker" 2>/dev/null
pkill -f "npm run dev" 2>/dev/null
sleep 2

# Start Redis
echo -e "${YELLOW}1️⃣  Redis (Message Queue)${NC}"
if command_exists redis-server; then
    redis-server --daemonize yes --logfile /tmp/redis.log
    sleep 2
    if port_in_use 6379; then
        echo -e "${GREEN}   ✅ Redis started on port 6379${NC}"
    else
        echo -e "${RED}   ❌ Redis failed to start${NC}"
        echo -e "${YELLOW}   Using in-memory queue fallback${NC}"
    fi
else
    echo -e "${YELLOW}   ⚠️  Redis not installed - using in-memory queue${NC}"
    echo -e "${YELLOW}   Install Redis for better performance: brew install redis${NC}"
fi
echo ""

# Start Backend
echo -e "${YELLOW}2️⃣  Backend API Server${NC}"
cd /Users/dustinbailey/Projects/cx/ai-doc-summary/backend
source venv/bin/activate

# Initialize database
python -c "from app.database import init_db; init_db()" 2>/dev/null

# Start backend
nohup python run_backend.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
sleep 3

if port_in_use 8000; then
    echo -e "${GREEN}   ✅ Backend running at http://localhost:8000${NC}"
else
    echo -e "${RED}   ❌ Backend failed to start${NC}"
    echo -e "${YELLOW}   Check logs: tail -f /tmp/backend.log${NC}"
fi
echo ""

# Start Celery Worker
echo -e "${YELLOW}3️⃣  Celery Worker (Job Processing)${NC}"
if port_in_use 6379 || [ "$DEMO_MODE" = "true" ]; then
    nohup celery -A app.celery_app worker --loglevel=info > /tmp/celery.log 2>&1 &
    CELERY_PID=$!
    sleep 3
    
    if pgrep -f "celery.*worker" > /dev/null; then
        echo -e "${GREEN}   ✅ Celery worker started${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Celery in eager mode (synchronous)${NC}"
    fi
else
    echo -e "${YELLOW}   ⚠️  Skipping Celery (no Redis)${NC}"
fi
echo ""

# Start Frontend
echo -e "${YELLOW}4️⃣  Frontend Application${NC}"
cd /Users/dustinbailey/Projects/cx/ai-doc-summary/frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}   Installing frontend dependencies...${NC}"
    npm install > /dev/null 2>&1
fi

nohup npm run dev -- --host 0.0.0.0 > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
sleep 5

if port_in_use 5173; then
    echo -e "${GREEN}   ✅ Frontend running at http://localhost:5173${NC}"
else
    echo -e "${RED}   ❌ Frontend failed to start${NC}"
    echo -e "${YELLOW}   Check logs: tail -f /tmp/frontend.log${NC}"
fi
echo ""

# Final Status
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ System Ready!${NC}"
echo ""
echo -e "${BLUE}📍 Access Points:${NC}"
echo -e "   Frontend:    ${GREEN}http://localhost:5173${NC}"
echo -e "   Backend API: ${GREEN}http://localhost:8000${NC}"
echo -e "   API Docs:    ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${BLUE}🎮 Demo Instructions:${NC}"
echo -e "   1. Open ${GREEN}http://localhost:5173${NC} in your browser"
echo -e "   2. Upload any document (PDF, DOCX, TXT, Image)"
echo -e "   3. Or use the Demo tab to generate test jobs"
echo -e "   4. Watch jobs process automatically!"
echo ""
echo -e "${BLUE}📊 Features Active:${NC}"
echo -e "   • Document upload and processing"
echo -e "   • AI provider simulation (no API keys needed)"
echo -e "   • Automatic job processing"
echo -e "   • Real-time dashboard updates"
echo -e "   • Cost estimation"
echo ""
echo -e "${YELLOW}📝 Logs:${NC}"
echo -e "   Backend:  tail -f /tmp/backend.log"
echo -e "   Celery:   tail -f /tmp/celery.log"
echo -e "   Frontend: tail -f /tmp/frontend.log"
echo -e "   Redis:    tail -f /tmp/redis.log"
echo ""
echo -e "${YELLOW}🛑 To stop all services:${NC}"
echo -e "   Press Ctrl+C or run: ./stop.sh"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Create stop script
cat > /Users/dustinbailey/Projects/cx/ai-doc-summary/stop.sh << 'EOF'
#!/bin/bash
echo "Stopping all services..."
pkill -f "redis-server"
pkill -f "uvicorn"
pkill -f "celery.*worker"
pkill -f "npm run dev"
echo "All services stopped."
EOF
chmod +x /Users/dustinbailey/Projects/cx/ai-doc-summary/stop.sh

# Keep script running and handle Ctrl+C
trap 'echo ""; echo "Stopping all services..."; ./stop.sh; exit 0' INT

# Monitor services
while true; do
    sleep 5
    
    # Check if services are still running
    if ! port_in_use 8000; then
        echo -e "${RED}⚠️  Backend stopped - restarting...${NC}"
        cd /Users/dustinbailey/Projects/cx/ai-doc-summary/backend
        source venv/bin/activate
        nohup python run_backend.py > /tmp/backend.log 2>&1 &
        sleep 3
    fi
    
    if ! pgrep -f "celery.*worker" > /dev/null && port_in_use 6379; then
        echo -e "${RED}⚠️  Celery stopped - restarting...${NC}"
        cd /Users/dustinbailey/Projects/cx/ai-doc-summary/backend
        source venv/bin/activate
        nohup celery -A app.celery_app worker --loglevel=info > /tmp/celery.log 2>&1 &
        sleep 3
    fi
done