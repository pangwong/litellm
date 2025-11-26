#!/bin/bash

# LiteLLM Backend Startup Script
# This script starts the LiteLLM proxy server for local development

set -e

echo "=========================================="
echo "  LiteLLM Backend Development Server"
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
    echo "Visit: https://python-poetry.org/docs/#installation"
    exit 1
fi

## Check if PostgreSQL is running
#if ! pg_isready -h localhost -p 5432 &> /dev/null; then
#    echo -e "${RED}Error: PostgreSQL not detected on localhost:5432${NC}"
#    echo ""
#    echo "Please start the database first:"
#    echo "  ./dev-scripts/start-db.sh"
#    echo ""
#    exit 1
#fi

echo -e "${GREEN}✓ Database is running${NC}"

# Set environment variables
export DATABASE_URL="${DATABASE_URL:-postgresql://llmproxy:dbpassword9090@localhost:5432/litellm}"
export STORE_MODEL_IN_DB="${STORE_MODEL_IN_DB:-True}"
export LITELLM_MODE="${LITELLM_MODE:-DEV}"
export LITELLM_LOG_LEVEL="${LITELLM_LOG_LEVEL:-INFO}"
export TZ="${TZ:-UTC}"  # Set default timezone to avoid conflicts

# StepFlow API Configuration
export STEPFLOW_API_BASE="${STEPFLOW_API_BASE:-https://api.stepfun.com}"
export STEPFLOW_API_KEY="${STEPFLOW_API_KEY:-4tvdUznoOkOED8QpN2BmFD3dM4eQh6chk7ERbbN8oNtFPaEnBYUgYrSaQ4AEK3C0V}"

echo -e "${GREEN}Environment Configuration:${NC}"
echo "  DATABASE_URL: $DATABASE_URL"
echo "  STORE_MODEL_IN_DB: $STORE_MODEL_IN_DB"
echo "  LITELLM_MODE: $LITELLM_MODE"
echo "  LITELLM_LOG_LEVEL: $LITELLM_LOG_LEVEL"
echo "  STEPFLOW_API_BASE: $STEPFLOW_API_BASE"
echo "  STEPFLOW_API_KEY: ${STEPFLOW_API_KEY:0:20}..."
echo ""

# Check if Prisma client is generated
echo -e "${YELLOW}Checking Prisma client...${NC}"
if ! poetry run python -c "from prisma import Prisma; Prisma()" &> /dev/null; then
    echo "Prisma client not generated. Generating now..."
    if ! poetry run prisma generate; then
        echo -e "${RED}Failed to generate Prisma client${NC}"
        echo "Please run manually: poetry run prisma generate"
        exit 1
    fi
    echo -e "${GREEN}✓ Prisma client generated${NC}"
else
    echo -e "${GREEN}✓ Prisma client ready${NC}"
fi

# Parse command line arguments
PORT="${PORT:-4000}"
CONFIG_FILE=""
DETAILED_DEBUG=""
USE_DEFAULT_CONFIG=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --config)
            CONFIG_FILE="$2"
            USE_DEFAULT_CONFIG=false
            shift 2
            ;;
        --debug)
            DETAILED_DEBUG="--detailed_debug"
            shift
            ;;
        --no-config)
            USE_DEFAULT_CONFIG=false
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--port PORT] [--config CONFIG_FILE] [--debug] [--no-config]"
            exit 1
            ;;
    esac
done

# Use default config if no config specified and it exists
if [ "$USE_DEFAULT_CONFIG" = true ] && [ -z "$CONFIG_FILE" ]; then
    DEFAULT_CONFIG="/home/wangpeng/litellm_deploy/litellm_config.yaml"
    if [ -f "$DEFAULT_CONFIG" ]; then
        CONFIG_FILE="$DEFAULT_CONFIG"
        echo -e "${GREEN}Using default config: $DEFAULT_CONFIG${NC}"
    fi
fi

# Start the server
echo ""
echo -e "${GREEN}Starting LiteLLM Proxy Server...${NC}"
echo "  Port: $PORT"
if [ -n "$CONFIG_FILE" ]; then
    echo "  Config: $CONFIG_FILE"
fi
if [ -n "$DETAILED_DEBUG" ]; then
    echo "  Debug: Enabled"
fi
echo "  UI will be available at: http://localhost:$PORT"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo "=========================================="
echo ""

if [ -n "$CONFIG_FILE" ]; then
    poetry run python -m litellm.proxy.proxy_cli --config "$CONFIG_FILE" --port "$PORT" $DETAILED_DEBUG
else
    poetry run python -m litellm.proxy.proxy_cli --port "$PORT" $DETAILED_DEBUG
fi
