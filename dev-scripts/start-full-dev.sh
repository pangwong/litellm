#!/bin/bash

# LiteLLM Full Development Environment Startup Script
# This script starts both backend and frontend in development mode

set -e

echo "=========================================="
echo "  LiteLLM Full Development Environment"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Detect which docker compose command to use
get_docker_compose_cmd() {
    if docker compose version &> /dev/null; then
        echo "docker compose"
    elif command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    else
        echo ""
    fi
}

DOCKER_COMPOSE=$(get_docker_compose_cmd)

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}Error: Poetry not found. Please install Poetry first.${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js not found. Please install Node.js v20+${NC}"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm not found. Please install npm${NC}"
    exit 1
fi

echo -e "${GREEN}Detected versions:${NC}"
echo "  Python: $(python3 --version)"
echo "  Node: $(node --version)"
echo "  npm: $(npm --version)"
echo ""

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    echo -e "${RED}Error: PostgreSQL not detected on localhost:5432${NC}"
    echo ""
    echo "Please start the database first:"
    echo "  ./dev-scripts/start-db.sh"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Database is running${NC}"

# Set environment variables for backend
export DATABASE_URL="${DATABASE_URL:-postgresql://llmproxy:dbpassword9090@localhost:5432/litellm}"
export STORE_MODEL_IN_DB="${STORE_MODEL_IN_DB:-True}"
export LITELLM_MODE="${LITELLM_MODE:-DEV}"
export LITELLM_LOG_LEVEL="${LITELLM_LOG_LEVEL:-INFO}"
export TZ="${TZ:-UTC}"  # Set default timezone to avoid conflicts

# StepFlow API Configuration
export STEPFLOW_API_BASE="${STEPFLOW_API_BASE:-https://api.stepfun.com}"
export STEPFLOW_API_KEY="${STEPFLOW_API_KEY:-2kZ2irJpqrVk94Fa3rRZkTW4kWYTX0K6qlWribKEkFmjbcoiQIeP7L0F9Kb5SJ1qA}"

# Check Prisma client
echo -e "${YELLOW}Checking Prisma client...${NC}"
if ! poetry run python -c "from prisma import Prisma; Prisma()" &> /dev/null; then
    echo "Prisma client not generated. Generating now..."
    if ! poetry run prisma generate; then
        echo -e "${RED}Failed to generate Prisma client${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Prisma client generated${NC}"
else
    echo -e "${GREEN}✓ Prisma client ready${NC}"
fi

# Check if UI dependencies are installed
if [ ! -d "ui/litellm-dashboard/node_modules" ]; then
    echo -e "${YELLOW}Installing UI dependencies...${NC}"
    cd ui/litellm-dashboard
    npm install
    cd ../..
fi

# Create log directory
mkdir -p logs

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down servers...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

echo ""
echo -e "${GREEN}Starting Backend Server (port 4000)...${NC}"
poetry run python -m litellm.proxy.proxy_cli --port 4000 > logs/backend.log 2>&1 &
BACKEND_PID=$!

echo "Waiting for backend to start..."
sleep 5

# Check if backend started successfully
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}Backend failed to start. Check logs/backend.log${NC}"
    exit 1
fi

echo -e "${GREEN}Backend started successfully (PID: $BACKEND_PID)${NC}"
echo ""

echo -e "${GREEN}Starting Frontend Dev Server (port 3000)...${NC}"
cd ui/litellm-dashboard
npm run dev > ../../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ../..

echo "Waiting for frontend to start..."
sleep 5

# Check if frontend started successfully
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}Frontend failed to start. Check logs/frontend.log${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}Frontend started successfully (PID: $FRONTEND_PID)${NC}"
echo ""

echo "=========================================="
echo -e "${GREEN}Development Environment Ready!${NC}"
echo "=========================================="
echo ""
echo "  Backend API:  http://localhost:4000"
echo "  Frontend UI:  http://localhost:3000"
echo ""
echo "  Backend logs:  tail -f logs/backend.log"
echo "  Frontend logs: tail -f logs/frontend.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"
echo ""

# Wait for user to stop
wait
