# Development Scripts

Helper scripts for running LiteLLM locally without Docker.

## Available Scripts

### Database Management

#### 1. `start-db.sh`

Starts the PostgreSQL database container.

**Usage:**
```bash
./dev-scripts/start-db.sh
```

**What it does:**
- Checks if database is already running
- Starts PostgreSQL container with Docker Compose
- Waits for database to be fully initialized (up to 30 seconds)
- Verifies connection is working
- Shows connection information

**When to use:**
- First time setup (once)
- After system restart
- After running `stop-db.sh` or `reset-db.sh`

**Note:** You only need to run this once. The database stays running until you stop it.

---

#### 2. `stop-db.sh`

Stops the PostgreSQL database container (data is preserved).

**Usage:**
```bash
./dev-scripts/stop-db.sh
```

**When to use:**
- When you're done developing and want to free up resources
- Before system shutdown (optional)

---

#### 3. `reset-db.sh`

Stops the database and deletes all data (fresh start).

**Usage:**
```bash
./dev-scripts/reset-db.sh
```

**What it does:**
- Prompts for confirmation
- Stops and removes database container
- Deletes the database volume (all data lost)

**When to use:**
- When you want to start with a clean database
- When testing migrations
- When database is corrupted

---

### Backend Scripts

#### 4. `start-backend.sh`

Starts only the LiteLLM proxy backend server.

**Usage:**
```bash
# Basic usage (port 4000)
./dev-scripts/start-backend.sh

# Custom port
./dev-scripts/start-backend.sh --port 4001

# With config file
./dev-scripts/start-backend.sh --config config.dev.yaml

# With debug logging
./dev-scripts/start-backend.sh --debug

# All options combined
./dev-scripts/start-backend.sh --port 4001 --config config.dev.yaml --debug
```

**What it does:**
- Checks database is running (errors if not)
- Sets up environment variables
- Generates Prisma client if needed
- Starts the proxy server
- Serves the pre-built UI at http://localhost:4000

**When to use:**
- When you only need to modify backend code
- When you're using the pre-built UI
- For faster startup (no frontend dev server)
- **Every time you update backend code**

---

#### 5. `start-full-dev.sh`

Starts both backend AND frontend in development mode.

**Usage:**
```bash
./dev-scripts/start-full-dev.sh
```

**What it does:**
- Checks database is running (errors if not)
- Starts backend proxy server on port 4000
- Starts frontend Next.js dev server on port 3000
- Creates logs in `logs/backend.log` and `logs/frontend.log`
- Enables hot reload for UI changes

**When to use:**
- When you're modifying UI/frontend code
- When you want live reload for UI changes
- For full-stack development

**Accessing:**
- Backend API: http://localhost:4000
- Frontend UI: http://localhost:3000 (with hot reload)

---

### UI Scripts

#### 6. `build-ui.sh`

Builds the Next.js UI and copies it to the proxy directory.

**Usage:**
```bash
./dev-scripts/build-ui.sh
```

**What it does:**
- Installs npm dependencies if needed
- Builds the Next.js production bundle
- Copies output to `litellm/proxy/_experimental/out/`
- Cleans up build artifacts

**When to use:**
- After making UI changes and before committing
- When you want to test the production build
- Before switching back to backend-only development

---

### Setup Scripts

#### 7. `setup.sh`

Interactive first-time setup script.

**Usage:**
```bash
./dev-scripts/setup.sh
```

**What it does:**
- Checks all prerequisites
- Installs Python dependencies
- Starts PostgreSQL
- Generates Prisma client
- Installs UI dependencies
- Guides you through API key setup

---

#### 8. `verify-setup.sh`

Verifies your development environment is configured correctly.

**Usage:**
```bash
./dev-scripts/verify-setup.sh
```

**What it does:**
- Checks system prerequisites
- Verifies Python environment
- Checks database status
- Verifies UI is built
- Checks port availability

---

## Quick Start Guide

### First Time Setup

```bash
# 1. Run the setup script
./dev-scripts/setup.sh

# Or manually:
make install-proxy-dev
poetry run prisma generate
./dev-scripts/start-db.sh
```

### Daily Development Workflow

#### Option 1: Backend Development Only (Recommended)

```bash
# One-time: Start database (stays running)
./dev-scripts/start-db.sh

# Every time you edit code: Restart backend
./dev-scripts/start-backend.sh
# Press Ctrl+C to stop, make changes, run again
```

#### Option 2: Frontend Development

```bash
# One-time: Start database
./dev-scripts/start-db.sh

# Start both backend and frontend with hot reload
./dev-scripts/start-full-dev.sh

# Make UI changes - they auto-reload in browser!

# When done: Build UI for production
./dev-scripts/build-ui.sh
```

#### Option 3: With Custom Config

```bash
# One-time: Start database
./dev-scripts/start-db.sh

# Edit config.dev.yaml with your settings
./dev-scripts/start-backend.sh --config config.dev.yaml
```

---

## Common Workflows

### Typical Development Session

```bash
# Morning: Start database (if not running)
./dev-scripts/start-db.sh

# Develop: Start backend, make changes, restart as needed
./dev-scripts/start-backend.sh
# Edit Python files...
# Ctrl+C to stop
./dev-scripts/start-backend.sh  # Restart to see changes

# Evening: Stop database (optional - can leave running)
./dev-scripts/stop-db.sh
```

### Testing a Fresh Database

```bash
# Reset database
./dev-scripts/reset-db.sh

# Start fresh
./dev-scripts/start-db.sh

# Start backend
./dev-scripts/start-backend.sh
```

### Frontend UI Development

```bash
# Start database (if not running)
./dev-scripts/start-db.sh

# Start full dev environment
./dev-scripts/start-full-dev.sh

# Edit files in ui/litellm-dashboard/src/
# Changes appear instantly at http://localhost:3000

# When done, build for production
Ctrl+C  # Stop servers
./dev-scripts/build-ui.sh
```

---

## Environment Variables

All scripts respect these environment variables:

- `DATABASE_URL` - PostgreSQL connection (default: postgresql://llmproxy:dbpassword9090@localhost:5432/litellm)
- `STORE_MODEL_IN_DB` - Enable model management UI (default: True)
- `LITELLM_MODE` - Set to DEV for development (default: DEV)
- `LITELLM_LOG_LEVEL` - Logging level (default: INFO)
- `PORT` - Backend port (default: 4000)

Plus all your LLM provider API keys:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `AZURE_API_KEY`
- etc.

---

## Logs

When using `start-full-dev.sh`, logs are written to:
- `logs/backend.log` - Backend server logs
- `logs/frontend.log` - Frontend dev server logs

View logs in real-time:
```bash
tail -f logs/backend.log
tail -f logs/frontend.log
```

Database logs:
```bash
docker compose logs db -f
```

---

## Troubleshooting

### "Database not detected"
```bash
./dev-scripts/start-db.sh
```

### "Port 4000 already in use"
```bash
lsof -i :4000
kill -9 <PID>
# Or use different port:
PORT=4001 ./dev-scripts/start-backend.sh
```

### "Prisma client not found"
```bash
poetry run prisma generate
```

### Database connection issues
```bash
# Check status
docker compose ps

# Check logs
docker compose logs db

# Restart
docker compose restart db

# Or reset
./dev-scripts/reset-db.sh
./dev-scripts/start-db.sh
```

### UI changes not reflecting
If using `start-backend.sh`, you need to rebuild:
```bash
./dev-scripts/build-ui.sh
# Restart backend
```

If using `start-full-dev.sh`, check:
- Frontend server is running (check logs/frontend.log)
- Accessing http://localhost:3000 (not 4000)
- Clear browser cache

---

## Architecture

### Separation of Concerns

**Database (start-db.sh)**
- Runs in Docker container
- Persistent data in volume
- Start once, keeps running
- Independent of code changes

**Backend (start-backend.sh)**
- Python/FastAPI app
- Connects to database
- Serves API + pre-built UI
- Restart after code changes

**Frontend Dev (start-full-dev.sh)**
- Next.js dev server
- Hot reload enabled
- Proxies API to backend
- Only for UI development

---

## See Also

- [LOCAL_DEV_SETUP.md](../LOCAL_DEV_SETUP.md) - Complete setup guide
- [CLAUDE.md](../CLAUDE.md) - Architecture and development guide
- [config.dev.yaml](../config.dev.yaml) - Sample configuration file
