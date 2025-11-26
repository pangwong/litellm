#!/bin/bash

# LiteLLM Quick Setup Script
# This script helps you set up LiteLLM for local development

set -e

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
echo "║  LiteLLM Local Development Setup      ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to prompt for input
prompt_continue() {
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 1
    fi
}

# Check prerequisites
echo -e "${BLUE}Step 1: Checking prerequisites...${NC}"
echo ""

PREREQ_OK=true

if command_exists python3; then
    echo -e "${GREEN}✓${NC} Python3: $(python3 --version)"
else
    echo -e "${RED}✗${NC} Python3 not found"
    PREREQ_OK=false
fi

if command_exists poetry; then
    echo -e "${GREEN}✓${NC} Poetry: $(poetry --version)"
else
    echo -e "${RED}✗${NC} Poetry not found"
    echo "  Install: curl -sSL https://install.python-poetry.org | python3 -"
    PREREQ_OK=false
fi

if command_exists node; then
    echo -e "${GREEN}✓${NC} Node.js: $(node --version)"
else
    echo -e "${RED}✗${NC} Node.js not found"
    echo "  Install: https://nodejs.org/ or use nvm"
    PREREQ_OK=false
fi

if command_exists docker; then
    echo -e "${GREEN}✓${NC} Docker: $(docker --version)"
else
    echo -e "${YELLOW}⚠${NC} Docker not found (optional, but recommended for PostgreSQL)"
fi

if [ -n "$DOCKER_COMPOSE" ]; then
    echo -e "${GREEN}✓${NC} Docker Compose: $($DOCKER_COMPOSE version)"
else
    echo -e "${YELLOW}⚠${NC} Docker Compose not found (optional)"
fi

if [ "$PREREQ_OK" = false ]; then
    echo ""
    echo -e "${RED}Some prerequisites are missing. Please install them first.${NC}"
    exit 1
fi

prompt_continue

# Install Python dependencies
echo ""
echo -e "${BLUE}Step 2: Installing Python dependencies...${NC}"
echo "This may take a few minutes..."
echo ""

if ! poetry install --with dev,proxy-dev --extras proxy; then
    echo -e "${RED}Failed to install dependencies${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Dependencies installed${NC}"

prompt_continue

# Start PostgreSQL
echo ""
echo -e "${BLUE}Step 3: Setting up PostgreSQL database...${NC}"
echo ""

if [ -n "$DOCKER_COMPOSE" ]; then
    echo "Starting PostgreSQL with Docker Compose..."
    $DOCKER_COMPOSE up -d db

    echo "Waiting for PostgreSQL to be ready..."
    sleep 5

    if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL is running${NC}"
    else
        echo -e "${YELLOW}⚠ PostgreSQL may not be ready yet${NC}"
        echo "Wait a few seconds and run: $DOCKER_COMPOSE ps"
    fi
else
    echo -e "${YELLOW}Docker Compose not found.${NC}"
    echo "Please install PostgreSQL manually or install Docker Compose."
    echo ""
    echo "Manual PostgreSQL setup:"
    echo "  1. Install PostgreSQL"
    echo "  2. Create database: createdb litellm"
    echo "  3. Create user: createuser -P llmproxy (password: dbpassword9090)"
fi

prompt_continue

# Generate Prisma client
echo ""
echo -e "${BLUE}Step 4: Generating Prisma client...${NC}"
echo ""

if ! poetry run prisma generate; then
    echo -e "${RED}Failed to generate Prisma client${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prisma client generated${NC}"

prompt_continue

# Install UI dependencies
echo ""
echo -e "${BLUE}Step 5: Installing UI dependencies...${NC}"
echo ""

cd ui/litellm-dashboard
npm install
cd ../..

echo -e "${GREEN}✓ UI dependencies installed${NC}"

# Check if UI is already built
echo ""
echo -e "${BLUE}Step 6: Checking UI build...${NC}"
echo ""

if [ -d "litellm/proxy/_experimental/out/_next" ]; then
    echo -e "${GREEN}✓ Pre-built UI found${NC}"
else
    echo -e "${YELLOW}⚠ UI not built yet${NC}"
    echo "You can build it now or later with: ./dev-scripts/build-ui.sh"
fi

# Setup environment variables
echo ""
echo -e "${BLUE}Step 7: Environment Configuration${NC}"
echo ""

echo "You'll need to set up your API keys as environment variables."
echo "Add these to your ~/.bashrc, ~/.zshrc, or .env file:"
echo ""
echo -e "${YELLOW}export DATABASE_URL=\"postgresql://llmproxy:dbpassword9090@localhost:5432/litellm\"${NC}"
echo -e "${YELLOW}export STORE_MODEL_IN_DB=\"True\"${NC}"
echo -e "${YELLOW}export OPENAI_API_KEY=\"sk-...\"${NC}"
echo -e "${YELLOW}export ANTHROPIC_API_KEY=\"sk-ant-...\"${NC}"
echo ""

read -p "Do you want to set these now for this session? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    export DATABASE_URL="postgresql://llmproxy:dbpassword9090@localhost:5432/litellm"
    export STORE_MODEL_IN_DB="True"

    read -p "Enter your OpenAI API key (or press Enter to skip): " OPENAI_KEY
    if [ -n "$OPENAI_KEY" ]; then
        export OPENAI_API_KEY="$OPENAI_KEY"
        echo -e "${GREEN}✓ OpenAI API key set${NC}"
    fi

    read -p "Enter your Anthropic API key (or press Enter to skip): " ANTHROPIC_KEY
    if [ -n "$ANTHROPIC_KEY" ]; then
        export ANTHROPIC_API_KEY="$ANTHROPIC_KEY"
        echo -e "${GREEN}✓ Anthropic API key set${NC}"
    fi
fi

# Summary
echo ""
echo "╔════════════════════════════════════════╗"
echo "║  Setup Complete!                       ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}You're ready to start developing!${NC}"
echo ""
echo "Choose your workflow:"
echo ""
echo -e "${BLUE}Option 1: Backend only (faster, uses pre-built UI)${NC}"
echo "  ./dev-scripts/start-backend.sh"
echo "  Access at: http://localhost:4000"
echo ""
echo -e "${BLUE}Option 2: Full dev (backend + frontend with hot reload)${NC}"
echo "  ./dev-scripts/start-full-dev.sh"
echo "  Backend: http://localhost:4000"
echo "  Frontend: http://localhost:3000"
echo ""
echo -e "${BLUE}Option 3: With custom config${NC}"
echo "  ./dev-scripts/start-backend.sh --config config.dev.yaml"
echo ""
echo "See LOCAL_DEV_SETUP.md for complete documentation."
echo ""

# Offer to start now
read -p "Start the backend server now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./dev-scripts/start-backend.sh
fi
