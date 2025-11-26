#!/bin/bash

# LiteLLM UI Build Script
# This script builds the Next.js UI and copies it to the proxy directory

set -e

echo "=========================================="
echo "  LiteLLM UI Build Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "ui/litellm-dashboard" ]; then
    echo -e "${RED}Error: Must run from litellm root directory${NC}"
    exit 1
fi

# Check Node version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo -e "${RED}Error: Node.js 18+ required (you have v$NODE_VERSION)${NC}"
    exit 1
fi

echo -e "${GREEN}Node.js version: $(node -v)${NC}"
echo ""

cd ui/litellm-dashboard

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    npm install
fi

echo -e "${GREEN}Building UI...${NC}"
echo ""

# Check if ui_colors.json exists, create default if not
if [ ! -f "ui_colors.json" ]; then
    echo -e "${YELLOW}Creating default ui_colors.json...${NC}"
    cat > ui_colors.json << 'EOF'
{
  "primary": "#6366f1",
  "secondary": "#8b5cf6"
}
EOF
fi

# Build the UI
npm run build

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}Build successful!${NC}"
    echo ""
    echo -e "${YELLOW}Copying files to proxy directory...${NC}"

    # Specify the destination directory
    destination_dir="../../litellm/proxy/_experimental/out"

    # Remove existing files in the destination directory
    rm -rf "$destination_dir"/*

    # Copy the contents of the output directory to the specified destination
    cp -r ./out/* "$destination_dir"

    # Remove build artifacts
    rm -rf ./out

    echo -e "${GREEN}UI build completed successfully!${NC}"
    echo ""
    echo "The UI has been built and copied to: litellm/proxy/_experimental/out/"
    echo ""
    echo "To use the new UI:"
    echo "  1. Restart your LiteLLM proxy server"
    echo "  2. Access the UI at http://localhost:4000"
else
    echo ""
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi

cd ../..
