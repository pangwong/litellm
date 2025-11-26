#!/bin/bash

# LiteLLM Database Reset Script
# This script stops the database and removes all data

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  LiteLLM Database Reset"
echo "=========================================="
echo ""
echo -e "${RED}WARNING: This will delete ALL database data!${NC}"
echo ""

# Prompt for confirmation
read -p "Are you sure you want to reset the database? (yes/no) " -r
echo ""
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Reset cancelled"
    exit 0
fi

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

# Stop and remove database container
echo "Stopping database container..."
$DOCKER_COMPOSE down

# Remove volume
echo "Removing database volume..."
if docker volume ls | grep -q litellm_postgres_data; then
    docker volume rm litellm_postgres_data
    echo -e "${GREEN}✓ Database volume removed${NC}"
else
    echo -e "${YELLOW}Volume not found (may already be removed)${NC}"
fi

echo ""
echo -e "${GREEN}Database reset complete!${NC}"
echo ""
echo "To start a fresh database: ./dev-scripts/start-db.sh"
echo ""
