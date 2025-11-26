#!/bin/bash

# LiteLLM Development Environment Verification Script
# This script checks if your local dev environment is properly configured

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

echo ""
echo "╔════════════════════════════════════════╗"
echo "║  LiteLLM Development Environment      ║"
echo "║  Verification Check                    ║"
echo "╚════════════════════════════════════════╝"
echo ""

ISSUES=0

# Function to check command
check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $2: $($1 --version 2>&1 | head -1)"
    else
        echo -e "${RED}✗${NC} $2: not found"
        ((ISSUES++))
    fi
}

# Function to check file
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2: not found"
        ((ISSUES++))
    fi
}

# Function to check directory
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2: not found"
        ((ISSUES++))
    fi
}

# Function to check environment variable
check_env() {
    if [ -n "${!1}" ]; then
        echo -e "${GREEN}✓${NC} $1 is set"
    else
        echo -e "${YELLOW}⚠${NC} $1: not set (optional)"
    fi
}

# Check System Prerequisites
echo -e "${BLUE}System Prerequisites:${NC}"
check_command python3 "Python"
check_command poetry "Poetry"
check_command node "Node.js"
check_command npm "npm"
check_command docker "Docker"
if [ -n "$DOCKER_COMPOSE" ]; then
    echo -e "${GREEN}✓${NC} Docker Compose: $($DOCKER_COMPOSE version | head -1)"
else
    echo -e "${YELLOW}⚠${NC} Docker Compose: not found"
fi
echo ""

# Check Python Environment
echo -e "${BLUE}Python Environment:${NC}"
if command -v poetry >/dev/null 2>&1; then
    if poetry run python -c "import litellm" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} LiteLLM package installed"
    else
        echo -e "${RED}✗${NC} LiteLLM package not installed"
        echo "  Run: make install-proxy-dev"
        ((ISSUES++))
    fi

    if poetry run python -c "import prisma" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Prisma client generated"
    else
        echo -e "${RED}✗${NC} Prisma client not generated"
        echo "  Run: poetry run prisma generate"
        ((ISSUES++))
    fi
fi
echo ""

# Check UI
echo -e "${BLUE}Frontend UI:${NC}"
check_dir "ui/litellm-dashboard" "UI source directory"
check_dir "ui/litellm-dashboard/node_modules" "UI dependencies installed"
check_dir "litellm/proxy/_experimental/out" "UI build directory"

if [ -d "litellm/proxy/_experimental/out/_next" ]; then
    echo -e "${GREEN}✓${NC} Pre-built UI exists"
else
    echo -e "${YELLOW}⚠${NC} UI not built (build with: ./dev-scripts/build-ui.sh)"
fi
echo ""

# Check Database
echo -e "${BLUE}Database:${NC}"
if docker ps | grep -q litellm_db; then
    echo -e "${GREEN}✓${NC} PostgreSQL container running"
elif pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} PostgreSQL running locally"
else
    echo -e "${YELLOW}⚠${NC} PostgreSQL not detected"
    echo "  Run: docker-compose up -d db"
fi
echo ""

# Check Scripts
echo -e "${BLUE}Development Scripts:${NC}"
check_file "dev-scripts/start-backend.sh" "Backend startup script"
check_file "dev-scripts/start-full-dev.sh" "Full dev startup script"
check_file "dev-scripts/build-ui.sh" "UI build script"
check_file "dev-scripts/setup.sh" "Setup script"
check_file "config.dev.yaml" "Sample config file"
echo ""

# Check Configuration Files
echo -e "${BLUE}Configuration Files:${NC}"
check_file "LOCAL_DEV_SETUP.md" "Setup documentation"
check_file "CLAUDE.md" "Architecture guide"
check_file "dev-scripts/README.md" "Scripts documentation"
echo ""

# Check Environment Variables
echo -e "${BLUE}Environment Variables:${NC}"
check_env "DATABASE_URL"
check_env "OPENAI_API_KEY"
check_env "ANTHROPIC_API_KEY"
check_env "LITELLM_MODE"
echo ""

# Check Ports
echo -e "${BLUE}Port Availability:${NC}"
if lsof -Pi :4000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠${NC} Port 4000 is in use"
else
    echo -e "${GREEN}✓${NC} Port 4000 is available (backend)"
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠${NC} Port 3000 is in use"
else
    echo -e "${GREEN}✓${NC} Port 3000 is available (frontend dev)"
fi

if lsof -Pi :5432 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Port 5432 is in use (PostgreSQL)"
else
    echo -e "${YELLOW}⚠${NC} Port 5432 is not in use"
fi
echo ""

# Summary
echo "════════════════════════════════════════"
if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo ""
    echo "You're ready to start development:"
    echo "  ./dev-scripts/start-backend.sh"
    echo "  or"
    echo "  ./dev-scripts/start-full-dev.sh"
else
    echo -e "${RED}✗ Found $ISSUES issue(s)${NC}"
    echo ""
    echo "Please address the issues above, then run:"
    echo "  ./dev-scripts/verify-setup.sh"
fi
echo "════════════════════════════════════════"
echo ""
