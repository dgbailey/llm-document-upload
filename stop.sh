#!/bin/bash
echo "Stopping all services..."
pkill -f "redis-server"
pkill -f "uvicorn"
pkill -f "celery.*worker"
pkill -f "npm run dev"
echo "All services stopped."
