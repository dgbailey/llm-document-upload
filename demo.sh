#!/bin/bash

echo "🚀 AI Document Summary - Demo Mode"
echo "=================================="
echo ""

# Check if Redis is running
if lsof -Pi :6379 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Redis is running"
else
    echo "⚠️  Starting Redis..."
    redis-server --daemonize yes
    sleep 2
fi

# Check if backend is running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Backend is running at http://localhost:8000"
else
    echo "⚠️  Starting backend..."
    cd /Users/dustinbailey/Projects/cx/ai-doc-summary/backend
    source venv/bin/activate
    python run_backend.py &
    sleep 3
fi

# Check if Celery worker is running
if pgrep -f "celery.*worker" > /dev/null ; then
    echo "✅ Celery worker is running"
else
    echo "⚠️  Starting Celery worker..."
    cd /Users/dustinbailey/Projects/cx/ai-doc-summary/backend
    source venv/bin/activate
    celery -A app.celery_app worker --loglevel=info &
    sleep 3
fi

# Check if frontend is running  
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Frontend is running at http://localhost:5173"
else
    echo "⚠️  Starting frontend..."
    cd /Users/dustinbailey/Projects/cx/ai-doc-summary/frontend
    npm run dev -- --host 0.0.0.0 &
    sleep 3
fi

echo ""
echo "🎉 Demo Mode Ready!"
echo ""
echo "📍 Access Points:"
echo "   Frontend:  http://localhost:5173"
echo "   Backend:   http://localhost:8000" 
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "💡 Quick Start:"
echo "   1. Open http://localhost:5173 in your browser"
echo "   2. Go to the 'Demo' tab"
echo "   3. Click 'Generate Jobs' to create test data"
echo "   4. Watch the jobs process in real-time!"
echo ""
echo "🔧 Services Running:"
echo "   • Redis (Message Queue)"
echo "   • FastAPI Backend"
echo "   • Celery Worker (Job Processing)"
echo "   • React Frontend"
echo ""
echo "⚠️  Note: Jobs will now process automatically!"
echo "   - Upload a document to see it processed"
echo "   - Processing takes 1-10 seconds (simulated)"
echo "   - 10% of jobs will randomly fail (for testing)"
echo ""
echo "Press Ctrl+C to stop the demo"

# Trap Ctrl+C to cleanup
trap 'echo ""; echo "Stopping services..."; pkill -f redis-server; pkill -f uvicorn; pkill -f celery; pkill -f "npm run dev"; echo "Demo stopped."; exit 0' INT

# Keep script running
while true; do
    sleep 1
done