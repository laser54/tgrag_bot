# Telegram RAG Bot - Work Plan

## Overview
One-command deploy (Docker) of a Telegram bot with RAG memory. Users can drop files, index them, and ask questions.

**Principles:** Simplicity > features, sane defaults, no GPU, works on Linux/x86_64 and Apple Silicon.

**Stack:** Python 3.12, aiogram v3 + FastAPI, Qdrant (vector DB), Ollama optional.

**Current Status:** ✅ T1 & T2 completed. ✅ T3.1 & T3.2 completed. 🚧 Bot ready for production deployment.

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
**Goal:** Bot works via webhooks locally (cloudflared) & on VPS (domain), HTTPS-only

#### T3.1 - Webhook Endpoint & Bot Handlers (45 min)
- [x] Add webhook endpoint to FastAPI: POST /webhook/telegram
- [x] Create tg/handlers.py: /start and /menu handlers
- [x] /start: short welcome
- [x] /menu: WebApp keyboard with WebAppInfo(url=WEBAPP_URL)
- [x] Respect ALLOWED_USER_IDS (optional filtering)
- [x] Configure aiogram for webhook mode only
- [x] Add logging for commands/errors
- [x] **TEST:** Webhook endpoint accepts requests, handlers work
- [x] **COMMIT:** `feat(bot): telegram bot with webhook handlers`

#### T3.2 - Local Development with cloudflared (45 min)
- [x] Add cloudflared Docker container to docker-compose
- [x] Create automatic cloudflared startup and webhook URL configuration
- [x] Add webhook setup/cleanup in FastAPI lifespan
- [x] Configure bot to use cloudflared HTTPS URL
- [x] **TEST:** Bot receives messages via cloudflared webhook locally
- [x] **COMMIT:** `feat(dev): cloudflared docker integration for local webhook development`

#### T3.3 - VPS Ubuntu Deployment (30 min)
- [ ] Create deploy/ubuntu-setup.sh script (2-3 commands)
- [ ] Install Python, pip, git, nginx, certbot on clean Ubuntu
- [ ] Setup systemd service for auto-start
- [ ] Configure HTTPS with Let's Encrypt (requires domain)
- [ ] Add production webhook URL configuration
- [ ] **TEST:** Deploy to clean Ubuntu VPS with domain attached
- [ ] **COMMIT:** `feat(deploy): ubuntu vps deployment script`

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
- [ ] **Local webhook development:** Bot receives messages via cloudflared HTTPS tunnel
- [ ] **VPS deployment:** Clean Ubuntu + domain → 2-3 commands → production bot
- [ ] **Webhook endpoint:** POST /webhook/telegram processes Telegram updates
- [ ] **Bot commands:** /start welcome, /menu shows WebApp button
- [ ] **HTTPS everywhere:** All communication via secure HTTPS
- [ ] **Docker production:** Full containerized deployment ready
- [ ] **Health monitoring:** GET /health returns {"status":"ok"}

## Testing Strategy
- ✅ After T1: pre-commit hooks work, basic linting passes
- ✅ After T2: health endpoint responds correctly
- 🚧 After T3.1: webhook endpoint accepts requests, bot handlers work
- ⏳ After T3.2: bot receives messages via cloudflared webhook locally
- ⏳ After T3.3: clean Ubuntu VPS deployment with domain works
- ⏳ After T4: Mini App loads and shows health status
- ⏳ After T5: Docker containers start successfully
- ⏳ After T6: All deployment scenarios work (local cloudflared + VPS)

## Commands Reference
```bash
# Setup
pre-commit install || true
pip install -r requirements.txt  # fallback if poetry fails

# Development & Production commands:

# 1. Local development with cloudflared (automatic HTTPS)
export TELEGRAM_BOT_TOKEN=your_token
python run.py  # automatically starts cloudflared and configures webhooks

# 2. Production on VPS with domain
# Deploy to clean Ubuntu server with domain attached:
bash deploy/ubuntu-setup.sh yourdomain.com
# That's it! Bot will be running with HTTPS

# 3. Manual webhook setup (for custom tunnels)
cloudflared tunnel --url http://localhost:8080  # get https://abc123.trycloudflare.com
export TELEGRAM_BOT_TOKEN=your_token
export WEBHOOK_URL=https://abc123.trycloudflare.com/webhook/telegram
python run.py

# Docker
docker compose up -d --build
curl http://localhost:8080/health
```

## Constraints & Guardrails
- **Webhooks only:** No polling, only HTTPS webhooks for all deployments ✅ IMPLEMENTED
- **HTTPS everywhere:** All communication via secure HTTPS (cloudflared/Let's Encrypt)
- **Domain required:** Production needs domain for Let's Encrypt certificates
- **Fail fast on env:** Exit with clear message if TELEGRAM_BOT_TOKEN missing
- **No RAG yet:** Qdrant runs but unused
- **Clean logs:** Structured INFO on start, WARN on missing config
- **Security:** Don't log tokens, restrict /menu to private chats
- **Simple deployment:** 2-3 commands setup on clean Ubuntu server
