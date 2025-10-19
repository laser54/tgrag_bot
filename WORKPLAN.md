# Telegram RAG Bot - Work Plan

## Overview
One-command deploy (Docker) of a Telegram bot with RAG memory. Users can drop files, index them, and ask questions.

**Principles:** Simplicity > features, sane defaults, no GPU, works on Linux/x86_64 and Apple Silicon.

**Stack:** Python 3.12, aiogram v3 + FastAPI, Qdrant (vector DB), Ollama optional.

**Current Status:** ✅ T1 & T2 completed. 🚧 Starting T3: Webhook-based Telegram bot.

## Project Structure
```
tgrag-bot/
├─ apps/bot/
│  ├─ main.py              # FastAPI + aiogram integration
│  ├─ settings.py          # Pydantic BaseSettings, env validation
│  ├─ tg/handlers.py       # /start, /menu
│  └─ routes/health.py     # GET /health
├─ webapp/                 # Mini App (stub)
│  ├─ index.html
│  ├─ app.js
│  └─ styles.css
├─ docker/
│  ├─ Dockerfile
│  └─ compose.yml
├─ data/                   # placeholder for future uploads
├─ .env.example
├─ pyproject.toml
├─ README.md
├─ LICENSE (MIT)
├─ .gitignore
├─ .editorconfig
├─ ruff.toml
└─ .pre-commit-config.yaml
```

## Work Tasks

### T1 - Repo Hygiene ✅ COMPLETED (45 min)
- [x] Add MIT LICENSE
- [x] Add .gitignore (Python, Node, Docker)
- [x] Add .editorconfig
- [x] Add ruff.toml (reasonable defaults) - moved to pyproject.toml
- [x] Add .pre-commit-config.yaml (ruff + trailing-whitespace + end-of-file-fixer)
- [x] Initialize Poetry/venv with dependencies (FastAPI, aiogram, pydantic-settings, etc.)
- [x] Create .env.example with required vars + webhook vars
- [x] Add professional README with badges and comprehensive docs
- [x] **TEST:** Install pre-commit hooks and run ✅ PASSED
- [x] **COMMIT:** Multiple commits with proper tooling setup

### T2 - FastAPI Application + Health Route ✅ COMPLETED (30 min)
- [x] Create apps/bot/main.py: FastAPI app with lifespan, CORS, logging, mount static /webapp/*
- [x] Create routes/health.py: GET /health returns {"status":"ok"}
- [x] Create settings.py: Pydantic BaseSettings with env validation (TELEGRAM_BOT_TOKEN required)
- [x] Add run.py script for proper Python path handling
- [x] **TEST:** Run server locally, curl /health returns ok ✅ PASSED
- [x] **COMMIT:** `feat(api): FastAPI app with /health and static webapp`

### T3 - Telegram Bot with Webhooks (120-150 min)
**Goal:** Bot works via webhooks, runs locally, deploys to Ubuntu with 2-3 commands

#### T3.1 - Webhook Infrastructure (30 min)
- [ ] Add webhook endpoint to FastAPI: POST /webhook/telegram
- [ ] Configure aiogram for webhook mode (not polling)
- [ ] Add webhook URL configuration (WEBHOOK_URL)
- [ ] **TEST:** Webhook endpoint accepts requests
- [ ] **COMMIT:** `feat(webhook): basic webhook endpoint infrastructure`

#### T3.2 - Bot Handlers (30 min)
- [ ] Create tg/handlers.py: /start and /menu handlers
- [ ] /start: short welcome + repo link
- [ ] /menu: WebApp keyboard with WebAppInfo(url=WEBAPP_URL)
- [ ] Respect ALLOWED_USER_IDS (optional filtering)
- [ ] Add logging for commands/errors
- [ ] **TEST:** Handlers process commands correctly
- [ ] **COMMIT:** `feat(bot): telegram bot handlers for /start and /menu`

#### T3.3 - Local Development with Tunneling (30 min)
- [ ] Add ngrok/pyngrok for local webhook tunneling
- [ ] Create dev script to setup webhook URL automatically
- [ ] Add webhook setup/cleanup in lifespan
- [ ] **TEST:** Bot receives messages via webhook in local dev
- [ ] **COMMIT:** `feat(dev): ngrok tunneling for local webhook development`

#### T3.4 - Ubuntu Server Deployment (30-60 min)
- [ ] Create deploy/ubuntu-setup.sh script
- [ ] Install Python, pip, git, nginx, certbot
- [ ] Setup systemd service for auto-start
- [ ] Configure HTTPS with Let's Encrypt
- [ ] Add production webhook URL setting
- [ ] **TEST:** Deploy to clean Ubuntu server with 2-3 commands
- [ ] **COMMIT:** `feat(deploy): ubuntu server deployment script`

### T4 - WebApp Stub (30-45 min)
- [ ] Create webapp/index.html: minimal page with Telegram WebApp SDK
- [ ] Create webapp/app.js: on load call /health, render status, handle SDK gracefully
- [ ] Create webapp/styles.css: mobile-friendly minimal styles
- [ ] **TEST:** Open in browser, verify health check works
- [ ] **COMMIT:** `feat(webapp): stub Mini App with health check`

### T5 - Docker & Compose (45-60 min)
- [ ] Create docker/Dockerfile: multi-stage build, expose 8080, run uvicorn
- [ ] Create docker/compose.yml: bot + qdrant services, volumes, optional ollama
- [ ] **TEST:** docker compose up -d --build, curl localhost:8080/health returns ok
- [ ] **COMMIT:** `chore(docker): Dockerfile and compose with qdrant`

### T6 - Docs Polish & Guardrails (30-45 min)
- [ ] Expand README: Quickstart (Docker, local run), Troubleshooting, Roadmap
- [ ] Add Makefile with make dev, make up, make down
- [ ] Ensure pre-commit install instructions
- [ ] **TEST:** Follow README instructions to verify setup works
- [ ] **COMMIT:** `docs: quickstart, troubleshooting, roadmap`

## Definition of Done
- [ ] **Local webhook development:** Bot receives messages via ngrok tunnel
- [ ] **Ubuntu deployment:** Clean Ubuntu server → 2-3 commands → working bot
- [ ] **Webhook endpoint:** POST /webhook/telegram processes Telegram updates
- [ ] **Bot commands:** /start welcome, /menu shows WebApp button
- [ ] **Docker production:** docker compose up -d --build → fully working
- [ ] **Health checks:** GET /health returns {"status":"ok"}
- [ ] **Documentation:** README covers all deployment scenarios

## Testing Strategy
- ✅ After T1: pre-commit hooks work, basic linting passes
- ✅ After T2: health endpoint responds correctly
- 🚧 After T3.1: webhook endpoint accepts POST requests
- ⏳ After T3.2: bot handlers process commands correctly
- ⏳ After T3.3: ngrok tunnel established, bot receives messages locally
- ⏳ After T3.4: Ubuntu deployment script works on clean server
- ⏳ After T4: Mini App loads and shows health status
- ⏳ After T5: Docker containers start successfully
- ⏳ After T6: Complete end-to-end verification (webhook + polling modes)

## Commands Reference
```bash
# Setup
pre-commit install || true
pip install -r requirements.txt  # fallback if poetry fails

# Local run (webhook mode)
export TELEGRAM_BOT_TOKEN=123:abc
export WEBHOOK_URL=https://abc123.ngrok.io/webhook/telegram
python run.py

# Local run (polling mode for testing)
export TELEGRAM_BOT_TOKEN=123:abc
export USE_WEBHOOKS=false
python run.py

# Docker
docker compose up -d --build
curl http://localhost:8080/health
```

## Constraints & Guardrails
- **Webhooks first:** Production uses webhooks, polling for local testing only
- **HTTPS required:** Webhooks need HTTPS (ngrok for local, Let's Encrypt for production)
- **Fail fast on env:** Exit with clear message if TELEGRAM_BOT_TOKEN missing
- **No RAG yet:** Qdrant runs but unused
- **Clean logs:** Structured INFO on start, WARN on missing config
- **Security:** Don't log tokens, restrict /menu to private chats
- **Ubuntu deployment:** 2-3 commands setup on clean Ubuntu server
