#!/bin/bash

# Test Script for StepFlow Models
# Tests all stepflow models configured in the LiteLLM proxy

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROXY_URL="${PROXY_URL:-http://localhost:4000}"
API_KEY="${API_KEY:-sk-WhHzgUfETQoJUeMOSRPCPw}"
TEST_PROMPT="Write a haiku about coding"

# List of all chat completion models
CHAT_MODELS=(
    "stepflow/claude-sonnet-4-20250514"
    "stepflow/gpt-4o"
    "stepflow/glm-4.6"
    "stepflow/minimax-m1"
    "stepflow/grok4-0709"
    "stepflow/gpt-5"
    "stepflow/gpt5-nano"
    "stepflow/gpt-4o-2024-11-20"
    "stepflow/kimi-k2-0905-preview"
    "stepflow/doubao-seed-1.6-vison"
    "stepflow/claude-sonnet-4-5-20250929"
    "stepflow/claude-sonnet-4-5-20250929-thinking"
    "stepflow/qwq-32b"
    "stepflow/qwen3-235b-a22b"
    "stepflow/qwen3-14b"
    "stepflow/qwen3-32b"
    "stepflow/deepseek-r1-0528-ali"
    "stepflow/deepseek-v3.1-terminus"
    "stepflow/deepseek-v3.1-think"
    "stepflow/gemini-2.5-pro-preview-03-25"
    "stepflow/gemini-2.5-flash-preview-04-17-thinking"
    "stepflow/gemini-2.5-flash-preview-05-20-thinking"
    "stepflow/gemini-2.5-pro-thinking"
)

# Embedding models
EMBEDDING_MODELS=(
    "stepflow/text-embedding-3-large"
)

echo "=========================================="
echo "  StepFlow Models Test Suite"
echo "=========================================="
echo ""
echo "Proxy URL: $PROXY_URL"
echo "Total Chat Models: ${#CHAT_MODELS[@]}"
echo "Total Embedding Models: ${#EMBEDDING_MODELS[@]}"
echo ""

# Parse command line arguments
TEST_MODE="all"
SPECIFIC_MODEL=""
VERBOSE=false
TEST_STREAMING=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --chat)
            TEST_MODE="chat"
            shift
            ;;
        --embedding)
            TEST_MODE="embedding"
            shift
            ;;
        --stream)
            TEST_STREAMING=true
            shift
            ;;
        --model)
            SPECIFIC_MODEL="$2"
            TEST_MODE="single"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --chat              Test only chat completion models"
            echo "  --embedding         Test only embedding models"
            echo "  --stream            Test streaming mode"
            echo "  --model MODEL_NAME  Test a specific model"
            echo "  --verbose           Show full response"
            echo "  --help              Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Function to test chat completion
test_chat_completion() {
    local model=$1
    echo -e "${BLUE}Testing: $model${NC}"

    if [ "$TEST_STREAMING" = true ]; then
        # Test streaming mode
        echo "  Mode: Streaming"
        local response=$(curl -N -s -w "\nHTTP_STATUS:%{http_code}" "$PROXY_URL/v1/chat/completions" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $API_KEY" \
            -d "{
                \"model\": \"$model\",
                \"messages\": [{\"role\": \"user\", \"content\": \"$TEST_PROMPT\"}],
                \"stream\": true,
                \"max_tokens\": 100
            }" 2>&1)

        # Check if we got any data: lines
        if echo "$response" | grep -q "data:"; then
            echo -e "${GREEN}✓ SUCCESS (Streaming)${NC}"
            if [ "$VERBOSE" = true ]; then
                echo "$response"
            else
                # Show first few chunks
                echo "$response" | head -n 5
            fi
        else
            echo -e "${RED}✗ FAILED (No streaming data)${NC}"
            echo "$response" | head -n 5
        fi
    else
        # Test non-streaming mode
        local response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$PROXY_URL/v1/chat/completions" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $API_KEY" \
            -d "{
                \"model\": \"$model\",
                \"messages\": [{\"role\": \"user\", \"content\": \"$TEST_PROMPT\"}],
                \"max_tokens\": 100
            }")

        local http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d':' -f2)
        local body=$(echo "$response" | sed '/HTTP_STATUS:/d')

        if [ "$http_status" = "200" ]; then
            echo -e "${GREEN}✓ SUCCESS${NC}"
            if [ "$VERBOSE" = true ]; then
                echo "$body" | jq -r '.choices[0].message.content' 2>/dev/null || echo "$body"
            else
                local content=$(echo "$body" | jq -r '.choices[0].message.content' 2>/dev/null | head -n 1)
                echo "  Response: ${content:0:80}..."
            fi
        else
            echo -e "${RED}✗ FAILED (HTTP $http_status)${NC}"
            if [ "$VERBOSE" = true ]; then
                echo "$body"
            else
                local error=$(echo "$body" | jq -r '.error.message' 2>/dev/null || echo "$body" | head -n 1)
                echo "  Error: $error"
            fi
        fi
    fi
    echo ""
}

# Function to test embedding
test_embedding() {
    local model=$1
    echo -e "${BLUE}Testing: $model${NC}"

    local response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$PROXY_URL/v1/embeddings" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $API_KEY" \
        -d "{
            \"model\": \"$model\",
            \"input\": \"This is a test embedding request\"
        }")

    local http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d':' -f2)
    local body=$(echo "$response" | sed '/HTTP_STATUS:/d')

    if [ "$http_status" = "200" ]; then
        echo -e "${GREEN}✓ SUCCESS${NC}"
        if [ "$VERBOSE" = true ]; then
            echo "$body"
        else
            local embedding_length=$(echo "$body" | jq -r '.data[0].embedding | length' 2>/dev/null)
            echo "  Embedding dimensions: $embedding_length"
        fi
    else
        echo -e "${RED}✗ FAILED (HTTP $http_status)${NC}"
        if [ "$VERBOSE" = true ]; then
            echo "$body"
        else
            local error=$(echo "$body" | jq -r '.error.message' 2>/dev/null || echo "$body" | head -n 1)
            echo "  Error: $error"
        fi
    fi
    echo ""
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}Warning: jq not installed. Response parsing will be limited.${NC}"
    echo "Install jq for better output: sudo apt-get install jq (Debian/Ubuntu)"
    echo ""
fi

# Check if proxy is running
echo -e "${YELLOW}Checking if proxy is running...${NC}"
if ! curl -s "$PROXY_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}Error: Cannot connect to proxy at $PROXY_URL${NC}"
    echo "Please start the proxy first:"
    echo "  ./dev-scripts/start-backend.sh"
    exit 1
fi
echo -e "${GREEN}✓ Proxy is running${NC}"
echo ""

# Run tests based on mode
case $TEST_MODE in
    "single")
        echo "=========================================="
        echo "  Testing Single Model"
        echo "=========================================="
        echo ""

        # Check if it's an embedding model
        if [[ " ${EMBEDDING_MODELS[@]} " =~ " ${SPECIFIC_MODEL} " ]]; then
            test_embedding "$SPECIFIC_MODEL"
        else
            test_chat_completion "$SPECIFIC_MODEL"
        fi
        ;;

    "chat")
        echo "=========================================="
        echo "  Testing Chat Completion Models"
        echo "=========================================="
        echo ""

        success_count=0
        fail_count=0

        for model in "${CHAT_MODELS[@]}"; do
            if test_chat_completion "$model"; then
                ((success_count++)) || true
            else
                ((fail_count++)) || true
            fi
        done

        echo "=========================================="
        echo "  Chat Models Summary"
        echo "=========================================="
        echo -e "Total: ${#CHAT_MODELS[@]}"
        echo -e "${GREEN}Passed: $success_count${NC}"
        echo -e "${RED}Failed: $fail_count${NC}"
        ;;

    "embedding")
        echo "=========================================="
        echo "  Testing Embedding Models"
        echo "=========================================="
        echo ""

        for model in "${EMBEDDING_MODELS[@]}"; do
            test_embedding "$model"
        done
        ;;

    "all")
        echo "=========================================="
        echo "  Testing All Models"
        echo "=========================================="
        echo ""

        success_count=0
        fail_count=0

        echo -e "${YELLOW}Chat Completion Models:${NC}"
        echo ""

        for model in "${CHAT_MODELS[@]}"; do
            test_chat_completion "$model"
            if [ $? -eq 0 ]; then
                ((success_count++)) || true
            else
                ((fail_count++)) || true
            fi
        done

        echo -e "${YELLOW}Embedding Models:${NC}"
        echo ""

        for model in "${EMBEDDING_MODELS[@]}"; do
            test_embedding "$model"
            if [ $? -eq 0 ]; then
                ((success_count++)) || true
            else
                ((fail_count++)) || true
            fi
        done

        echo "=========================================="
        echo "  Overall Summary"
        echo "=========================================="
        total=$((${#CHAT_MODELS[@]} + ${#EMBEDDING_MODELS[@]}))
        echo -e "Total Models: $total"
        echo -e "${GREEN}Passed: $success_count${NC}"
        echo -e "${RED}Failed: $fail_count${NC}"
        ;;
esac

echo ""
echo "Testing complete!"
