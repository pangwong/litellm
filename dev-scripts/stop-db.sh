#!/bin/bash

# LiteLLM Database Stop Script
# This script stops the PostgreSQL database

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  LiteLLM Database Stop"
echo "=========================================="
echo ""

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

if [ -z "$DOCKER_COMPOSE" ]; then
    echo -e "${RED}Error: Docker Compose not found${NC}"
    exit 1
fi

# Check if database is running
if ! docker ps | grep -q litellm_db; then
    echo -e "${YELLOW}Database is not running${NC}"
    exit 0
fi

# Stop the database
echo "Stopping PostgreSQL container..."
$DOCKER_COMPOSE stop db

echo ""
echo -e "${GREEN}✓ Database stopped${NC}"
echo ""
echo "Data is preserved in volume: litellm_postgres_data"
echo ""
echo "To start again: ./dev-scripts/start-db.sh"
echo "To remove all data: ./dev-scripts/reset-db.sh"
echo ""
