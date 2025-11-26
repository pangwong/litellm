# Local Development Setup for LiteLLM

This guide helps you set up a local development environment for LiteLLM with UI, avoiding slow Docker builds.

## Prerequisites

- **Python**: 3.8.1+ (you have 3.10.12 ✓)
- **Node.js**: v20 (you have v24.9.0 ✓)
- **PostgreSQL**: 16+ (for database)
- **Poetry**: For Python package management
- **npm/nvm**: For frontend development

## Quick Start

### 1. Start PostgreSQL Database

You can use Docker for just the database:

```bash
# Start only the PostgreSQL container from docker-compose
docker compose up -d db

# Or install PostgreSQL locally and create database:
# createdb litellm
# psql litellm
```

**Note:** Use `docker compose` (V2, with space) instead of `docker-compose` (V1, with hyphen). The scripts will automatically detect which version you have.

Database connection info:
- **Host**: localhost
- **Port**: 5432
- **Database**: litellm
- **User**: llmproxy
- **Password**: dbpassword9090

### 2. Backend Setup (Python/FastAPI)

```bash
# Install dependencies
make install-proxy-dev

# Or manually:
poetry install --with dev,proxy-dev --extras proxy

# Generate Prisma client (REQUIRED - must run after dependency install)
poetry run prisma generate

# Set environment variables
export DATABASE_URL="postgresql://llmproxy:dbpassword9090@localhost:5432/litellm"
export STORE_MODEL_IN_DB="True"  # Enable UI model management
export LITELLM_MODE="DEV"
export LITELLM_LOG_LEVEL="DEBUG"

# Optional: Set your API keys for testing
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
# Add other provider API keys as needed
```

### 3. Option A: Run with Pre-built UI (Faster)

If you don't need to modify the UI:

```bash
# The UI is already built in litellm/proxy/_experimental/out/
# Just start the proxy server
poetry run python -m litellm.proxy.proxy_cli --port 4000 --detailed_debug

# Or with a config file:
poetry run python -m litellm.proxy.proxy_cli --config config.yaml --port 4000
```

Access the UI at: **http://localhost:4000**

### 4. Option B: Run with UI Development Mode (For UI Changes)

If you need to modify and see live UI changes:

**Terminal 1 - Backend:**
```bash
# Start backend proxy server
poetry run python -m litellm.proxy.proxy_cli --port 4000 --detailed_debug
```

**Terminal 2 - Frontend:**
```bash
# Navigate to UI directory
cd ui/litellm-dashboard

# Install dependencies (first time only)
npm install

# Start development server with hot reload
npm run dev

# The UI will run on http://localhost:3000 by default
# It will proxy API requests to http://localhost:4000
```

Access the development UI at: **http://localhost:3000**

### 5. Build UI for Production (When Ready)

When you're done with UI changes and want to use the built version:

```bash
cd ui/litellm-dashboard

# Build the UI (requires Node v20)
./build_ui.sh

# This will:
# 1. Build the Next.js app
# 2. Copy output to litellm/proxy/_experimental/out/
# 3. Now restart your proxy server to use the new build
```

## Helper Scripts

We've created helper scripts to make this easier:

### Start Backend Only
```bash
./dev-scripts/start-backend.sh
```

### Start Both Backend and Frontend (Dev Mode)
```bash
./dev-scripts/start-full-dev.sh
```

### Build UI
```bash
./dev-scripts/build-ui.sh
```

## Configuration

### Sample Config File

Create a `config.dev.yaml` for local testing:

```yaml
model_list:
  - model_name: gpt-4
    litellm_params:
      model: openai/gpt-4
      api_key: os.environ/OPENAI_API_KEY

  - model_name: claude-3-5-sonnet
    litellm_params:
      model: anthropic/claude-3-5-sonnet-20241022
      api_key: os.environ/ANTHROPIC_API_KEY

general_settings:
  master_key: sk-1234  # For testing - DO NOT use in production
  database_url: postgresql://llmproxy:dbpassword9090@localhost:5432/litellm
  store_model_in_db: true

litellm_settings:
  success_callback: ["langfuse"]  # Optional: enable logging
  drop_params: true
  set_verbose: true
```

Run with config:
```bash
poetry run python -m litellm.proxy.proxy_cli --config config.dev.yaml --port 4000
```

## Common Tasks

### Run Tests

```bash
# All tests
make test

# Unit tests only (fast)
make test-unit

# Specific test file
poetry run pytest tests/path/to/test_file.py -v

# With coverage
poetry run pytest tests/ --cov=litellm
```

### Code Quality

```bash
# Format code
make format

# Lint
make lint

# Type check
make lint-mypy
```

### Database Migrations

```bash
# Generate Prisma client after schema changes
poetry run prisma generate

# Create migration
poetry run prisma migrate dev --name my_migration

# Apply migrations
poetry run prisma migrate deploy

# View database in browser
poetry run prisma studio
```

### Reset Database

```bash
# Stop containers
docker compose down

# Remove volume
docker volume rm litellm_postgres_data

# Start fresh
docker compose up -d db
```

## Troubleshooting

### Issue: Prisma client not found
```bash
# Regenerate Prisma client
poetry run prisma generate
```

### Issue: Port 4000 already in use
```bash
# Find process using port
lsof -i :4000

# Kill process
kill -9 <PID>

# Or use different port
poetry run python -m litellm.proxy.proxy_cli --port 4001
```

### Issue: Database connection failed
```bash
# Check PostgreSQL is running
docker compose ps

# Check connection
psql postgresql://llmproxy:dbpassword9090@localhost:5432/litellm -c "SELECT 1"

# Restart database
docker compose restart db
```

### Issue: UI not loading
```bash
# Check if built UI exists
ls -la litellm/proxy/_experimental/out/

# Rebuild UI if missing
cd ui/litellm-dashboard && ./build_ui.sh
```

### Issue: Frontend dev server not proxying to backend
```bash
# Check ui/litellm-dashboard/next.config.mjs for proxy settings
# Ensure backend is running on port 4000
# Check ui/litellm-dashboard/.env.development
```

## Architecture Overview

### Backend Flow
1. Start server → `poetry run python -m litellm.proxy.proxy_cli`
2. Starts FastAPI server → `litellm/proxy/proxy_server.py`
3. Routes requests → `litellm/proxy/route_llm_request.py`
4. Serves UI from → `litellm/proxy/_experimental/out/`

### Frontend Flow (Dev Mode)
1. Next.js dev server on port 3000
2. Proxies API calls to backend on port 4000
3. Hot reload on file changes
4. Build output goes to `out/` directory

### Frontend Flow (Production)
1. Built static files in `litellm/proxy/_experimental/out/`
2. Served directly by FastAPI backend
3. All on single port (4000)

## Performance Tips

1. **Use Development UI Mode**: For UI changes, use `npm run dev` instead of rebuilding each time
2. **Database**: Use Docker PostgreSQL or local installation, both are fast
3. **Backend**: Run directly with `poetry run` instead of Docker
4. **Caching**: Use Redis for better performance (optional)
   ```bash
   docker run -d -p 6379:6379 redis:alpine
   export REDIS_HOST=localhost
   export REDIS_PORT=6379
   ```

## Environment Variables Reference

### Required
- `DATABASE_URL` - PostgreSQL connection string
- `STORE_MODEL_IN_DB` - Enable model management UI

### Optional
- `LITELLM_MODE` - Set to "DEV" for development
- `LITELLM_LOG_LEVEL` - DEBUG, INFO, WARNING, ERROR
- `REDIS_HOST` - Redis host for caching
- `REDIS_PORT` - Redis port
- `MASTER_KEY` - API key for proxy authentication

### Provider API Keys
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `AZURE_API_KEY` - Azure OpenAI key
- (See docs for all 100+ providers)

## Next Steps

1. **Modify Backend Code**: Edit files in `litellm/` and restart server
2. **Modify Frontend Code**: Edit files in `ui/litellm-dashboard/src/` (auto-reload in dev mode)
3. **Add New Provider**: Follow guide in CLAUDE.md
4. **Write Tests**: Add tests in `tests/` directory
5. **Check Logs**: Backend logs show in terminal, check for errors

## Useful Commands

```bash
# Backend health check
curl http://localhost:4000/health

# Test completion endpoint
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# View all routes
curl http://localhost:4000/openapi.json

# Prisma Studio (database UI)
poetry run prisma studio
```

## Resources

- [Official Docs](https://docs.litellm.ai/)
- [Proxy Docs](https://docs.litellm.ai/docs/simple_proxy)
- [Provider Docs](https://docs.litellm.ai/docs/providers)
- [CLAUDE.md](./CLAUDE.md) - Architecture and development guide
