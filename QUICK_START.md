# LiteLLM Local Development - Quick Reference

## 🚀 New Simplified Workflow

The database and backend are now **completely separate**!

### One-Time Setup

```bash
# 1. Install dependencies
make install-proxy-dev

# 2. Generate Prisma client
poetry run prisma generate

# 3. Start database (only once!)
./dev-scripts/start-db.sh
```

### Daily Development

```bash
# Just restart backend after code changes!
./dev-scripts/start-backend.sh

# Edit Python files in litellm/
# Press Ctrl+C and restart to see changes
```

---

## 📂 All Available Scripts

### Database Management
- `./dev-scripts/start-db.sh` - Start database (run once, stays running)
- `./dev-scripts/stop-db.sh` - Stop database
- `./dev-scripts/reset-db.sh` - Delete all data and start fresh

### Backend Development
- `./dev-scripts/start-backend.sh` - Start backend only ⭐ **Most used!**
- `./dev-scripts/start-backend.sh --config config.dev.yaml` - With custom config
- `./dev-scripts/start-backend.sh --debug` - With debug logging

### Full-Stack Development
- `./dev-scripts/start-full-dev.sh` - Start backend + frontend (for UI work)
- `./dev-scripts/build-ui.sh` - Build UI for production

### Setup & Verification
- `./dev-scripts/setup.sh` - Interactive first-time setup
- `./dev-scripts/verify-setup.sh` - Check if everything is configured

---

## 💡 Typical Workflow

### First Time (Once)

```bash
# Run the setup script - it does everything!
./dev-scripts/start-db.sh
```

### Every Day

```bash
# 1. Check if database is running
docker compose ps

# 2. If not, start it
./dev-scripts/start-db.sh

# 3. Start backend and develop
./dev-scripts/start-backend.sh

# Edit code...
# Press Ctrl+C
# Run again to see changes
./dev-scripts/start-backend.sh
```

### End of Day (Optional)

```bash
# Stop database to free up resources
./dev-scripts/stop-db.sh

# Or leave it running - it doesn't use much!
```

---

## 🔧 Why This is Better

### Old Way (Problem)
```bash
./dev-scripts/start-backend.sh
# Tries to start database
# Waits 5 seconds
# But database not ready yet!
# ❌ Authentication failed
```

### New Way (Solution)
```bash
# Step 1: Start database once
./dev-scripts/start-db.sh
# ✅ Waits up to 30 seconds
# ✅ Verifies it's ready
# ✅ Shows connection info

# Step 2: Restart backend as many times as you want
./dev-scripts/start-backend.sh  # Works!
# Edit code...
./dev-scripts/start-backend.sh  # Works!
# Edit code...
./dev-scripts/start-backend.sh  # Works!
```

---

## 🎯 Quick Commands

```bash
# Morning: Start database
./dev-scripts/start-db.sh

# Develop: Edit code, restart backend
./dev-scripts/start-backend.sh

# View logs
docker compose logs db -f

# Check database status
docker compose ps

# Reset if needed
./dev-scripts/reset-db.sh
./dev-scripts/start-db.sh

# Evening: Optionally stop (or leave running)
./dev-scripts/stop-db.sh
```

---

## 🐛 Troubleshooting

### "Database not detected"
```bash
./dev-scripts/start-db.sh
```

### "Authentication failed"
```bash
# Database wasn't fully initialized
./dev-scripts/reset-db.sh
./dev-scripts/start-db.sh
```

### "Port already in use"
```bash
lsof -i :4000
kill -9 <PID>
```

### Check everything is working
```bash
./dev-scripts/verify-setup.sh
```

---

## 🎨 For UI Development

```bash
# Start database
./dev-scripts/start-db.sh

# Start full dev environment (backend + frontend)
./dev-scripts/start-full-dev.sh
# Backend: http://localhost:4000
# Frontend: http://localhost:3000 (hot reload!)

# Edit files in ui/litellm-dashboard/src/
# Changes appear instantly!

# When done, build for production
./dev-scripts/build-ui.sh
```

---

## 📊 Database Info

**Connection String:**
```
postgresql://llmproxy:dbpassword9090@localhost:5432/litellm
```

**Container Name:** `litellm_db`

**Volume Name:** `litellm_postgres_data`

---

## 🔑 Environment Variables

Set these before starting backend:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or add to `~/.bashrc` or `~/.zshrc`:

```bash
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.bashrc
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.bashrc
source ~/.bashrc
```

---

## 📚 More Info

- **Detailed Guide:** `LOCAL_DEV_SETUP.md`
- **Scripts Documentation:** `dev-scripts/README.md`
- **Architecture:** `CLAUDE.md`
- **Sample Config:** `config.dev.yaml`

---

## ✅ Success Indicators

When everything is working:

```bash
$ ./dev-scripts/start-db.sh
✓ Database is already running
✓ Database is accepting connections

$ ./dev-scripts/start-backend.sh
✓ Database is running
✓ Prisma client ready

   ██╗     ██╗████████╗███████╗██╗     ██╗     ███╗   ███╗
   ...

INFO:     Uvicorn running on http://0.0.0.0:4000
```

Visit: **http://localhost:4000** 🎉

---

## 🚦 Current Status

Try these commands to check what's running:

```bash
# Check database
docker compose ps

# Check backend
lsof -i :4000

# Check all
./dev-scripts/verify-setup.sh
```
