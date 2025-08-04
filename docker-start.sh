#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}       🐳 AI Document Summary - Docker Demo Mode${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed!${NC}"
    echo -e "${YELLOW}Please install Docker Desktop from: https://www.docker.com/products/docker-desktop${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    echo -e "${YELLOW}Please start Docker Desktop and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is ready${NC}"
echo ""

# Stop any existing containers
echo -e "${YELLOW}🧹 Cleaning up existing containers...${NC}"
docker-compose down 2>/dev/null

# Build and start services
echo -e "${BLUE}🔨 Building Docker images...${NC}"
echo -e "${YELLOW}   This may take a few minutes on first run...${NC}"
docker-compose build

echo ""
echo -e "${BLUE}🚀 Starting services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo ""
echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"

# Function to check if service is healthy
check_health() {
    local service=$1
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps $service | grep -q "healthy\|Up"; then
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    return 1
}

# Check each service
echo -n "   Redis... "
if check_health redis; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
fi

echo -n "   PostgreSQL... "
if check_health postgres; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
fi

echo -n "   Backend... "
if check_health backend; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
fi

echo -n "   Celery Worker... "
if check_health celery; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
fi

echo -n "   Frontend... "
if check_health frontend; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
fi

# Initialize database
echo ""
echo -e "${BLUE}📊 Initializing database...${NC}"
docker-compose exec -T backend python -c "from app.database import init_db; init_db()" 2>/dev/null

echo ""
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ System Ready!${NC}"
echo ""
echo -e "${BLUE}📍 Access Points:${NC}"
echo -e "   Frontend:    ${GREEN}http://localhost:3000${NC}"
echo -e "   Backend API: ${GREEN}http://localhost:8000${NC}"
echo -e "   API Docs:    ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${BLUE}🎮 Demo Instructions:${NC}"
echo -e "   1. Open ${GREEN}http://localhost:3000${NC} in your browser"
echo -e "   2. Upload any document (PDF, DOCX, TXT, Image)"
echo -e "   3. Or use the Demo tab to generate test jobs"
echo -e "   4. Watch jobs process automatically with Celery!"
echo ""
echo -e "${BLUE}📊 Services Running:${NC}"
echo -e "   • Redis (Message Queue)"
echo -e "   • PostgreSQL (Database)"
echo -e "   • FastAPI Backend (API Server)"
echo -e "   • Celery Worker (Job Processing)"
echo -e "   • React Frontend (Web UI)"
echo ""
echo -e "${YELLOW}📝 Useful Commands:${NC}"
echo -e "   View logs:        ${BLUE}docker-compose logs -f [service]${NC}"
echo -e "   Stop all:         ${BLUE}docker-compose down${NC}"
echo -e "   Restart service:  ${BLUE}docker-compose restart [service]${NC}"
echo -e "   View containers:  ${BLUE}docker-compose ps${NC}"
echo ""
echo -e "${YELLOW}🛑 To stop all services:${NC}"
echo -e "   Run: ${BLUE}docker-compose down${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"