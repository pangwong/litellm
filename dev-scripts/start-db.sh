#!/bin/bash

# LiteLLM Database Management Script
# This script sets up and starts the PostgreSQL database for LiteLLM

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  LiteLLM Database Setup"
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
    echo "Please install Docker Compose first"
    exit 1
fi

# Check if database is already running
if docker ps | grep -q litellm_db; then
    echo -e "${GREEN}✓ Database is already running${NC}"
    echo ""
    echo "Database info:"
    echo "  Host: localhost"
    echo "  Port: 5432"
    echo "  Database: litellm"
    echo "  User: llmproxy"
    echo "  Password: dbpassword9090"
    echo ""
    echo "Connection string:"
    echo "  postgresql://llmproxy:dbpassword9090@localhost:5432/litellm"
    echo ""

    # Check if it's responding
    if docker compose exec -T db pg_isready -U llmproxy >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Database is accepting connections${NC}"
    else
        echo -e "${YELLOW}⚠ Database container is running but not ready yet${NC}"
        echo "Wait a few seconds and try again"
    fi

    exit 0
fi

# Start the database
echo "Starting PostgreSQL container..."
$DOCKER_COMPOSE up -d db

echo ""
echo "Waiting for PostgreSQL to initialize..."
echo "This may take 10-15 seconds for first-time setup..."
echo ""

# Wait for container to be healthy
MAX_WAIT=30
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if docker compose exec -T db pg_isready -U llmproxy >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Database is ready!${NC}"
        break
    fi

    echo -n "."
    sleep 1
    WAITED=$((WAITED + 1))
done

echo ""
echo ""

if [ $WAITED -eq $MAX_WAIT ]; then
    echo -e "${YELLOW}⚠ Database took longer than expected to start${NC}"
    echo "Check logs with: docker compose logs db"
    exit 1
fi

# Verify connection
echo "Verifying database connection..."
if docker compose exec -T db psql -U llmproxy -d litellm -c "SELECT 1;" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Successfully connected to database${NC}"
else
    echo -e "${RED}✗ Failed to connect to database${NC}"
    echo "Check logs with: docker compose logs db"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Database Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Database info:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: litellm"
echo "  User: llmproxy"
echo "  Password: dbpassword9090"
echo ""
echo "Connection string:"
echo "  postgresql://llmproxy:dbpassword9090@localhost:5432/litellm"
echo ""
echo "You can now start the backend with:"
echo "  ./dev-scripts/start-backend.sh"
echo ""
echo "Useful commands:"
echo "  docker compose logs db -f    # View database logs"
echo "  docker compose stop db       # Stop database"
echo "  docker compose restart db    # Restart database"
echo "  ./dev-scripts/stop-db.sh     # Stop database"
echo "  ./dev-scripts/reset-db.sh    # Reset database (deletes all data)"
echo ""
