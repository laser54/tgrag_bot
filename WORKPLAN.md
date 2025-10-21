# Telegram RAG Bot - Work Plan

## Overview
One-command deploy (Docker) of a Telegram bot with RAG memory. Users can drop files, index them, and ask questions.

**Principles:** Simplicity > features, sane defaults, no GPU, works on Linux/x86_64 and Apple Silicon.

**Stack:** Python 3.12, aiogram v3 + FastAPI, Qdrant (vector DB), Ollama optional.

**Current Status:** ✅ T1-T3.3 delivered. ✅ Docker packaging in place. 🚧 Telegram Mini App UX & wiring underway. ⏳ Documentation polish pending.

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

#### T3.3 - VPS Ubuntu Deployment (45-60 min)
- [x] Create `deploy/ubuntu-setup.sh`: single-run script taking domain + token
- [x] Validate clean Ubuntu 22.04/24.04, DNS A record, open ports 80/443
- [x] Install Docker CE + compose plugin, git, and base utilities
- [x] Launch Traefik/bot/Qdrant stack with automatic TLS
- [x] Ensure webhook env + `.env`/systemd handled automatically
- [x] Auto-stop conflicting services, clean previous runs, set webhook
- [x] **TEST:** Deploy on clean VPS → bot responds via HTTPS 443
- [x] **COMMIT:** `feat(deploy): ubuntu traefik autopilot`

### T4 - Telegram WebApp (Document Hub Mini App) (~2-3 days)
**Goal:** Ship a production-grade Telegram Mini App that feels native, manages documents, and exposes model controls. Backing API calls remain stubs but with real UX flows and request scaffolding.

#### T4.1 - UX Skeleton & Visual Language (0.5 day)
- [ ] Create `webapp/index.html` with three primary panels: `Document Library`, `Assistant Brain`, `Model Router`.
- [ ] Wire Telegram WebApp SDK init, theme sync, and responsive layout rules.
- [ ] Implement `styles.css` with modern mobile-first styling (glassmorphism cards, soft shadows, accent gradient CTA buttons).
- [ ] Add empty-state illustrations/placeholders (SVG or emoji) for document list and model selector.

#### T4.2 - Document Workflow Hooks (0.75 day)
- [ ] Surface upload dropzone + file picker (`dragover` + `click`) with post-upload status toasts.
- [ ] Render document table with columns: `Name`, `Uploaded`, `Indexed`, `Actions`.
- [ ] Add action buttons: `Add to Index` (POST stub), `Remove from Index` (DELETE stub), `Delete File` (DELETE stub) with optimistic UI and rollback notifications.
- [ ] Stub API layer in `app.js` exposing methods: `listDocuments()`, `uploadDocument(file)`, `indexDocument(id)`, `removeFromIndex(id)`, `deleteDocument(id)` that currently resolve mocked responses.

#### T4.3 - Assistant Brain Controls (0.5 day)
- [ ] Embed system prompt editor with live character counter, reset-to-default, and save stub button.
- [ ] Store prompt draft in local state with autosave indicator (spins on async stub request).
- [ ] Display current embeddings/model backend for context (read from stub config endpoint).
- [ ] Document expected REST endpoints: `GET/PUT /api/settings/prompt`, `GET /api/settings/llm`.

#### T4.4 - Model Router & API Providers (0.5 day)
- [ ] Build provider cards for `Local Ollama`, `OpenAI Compatible`, `Azure OpenAI`, `Custom HTTP` with selection radio buttons.
- [ ] Add modal/sheet for entering API base URL, key, and model name with validation patterns.
- [ ] Persist selection to state + stub `PUT /api/settings/provider` call.
- [ ] Indicate active provider + health using status pill (badge element).

#### T4.5 - Glue Code, QA & Delivery (0.75 day)
- [ ] Centralize app state (simple store or signals) to keep UI reactive without frameworks.
- [ ] Implement toast/snackbar utility + loading spinner overlay for long ops.
- [ ] Write `README` section describing Mini App, controls, and future backend expectations.
- [ ] **TEST:** Run locally via `python -m http.server` or FastAPI static mount, validate flows in Telegram browser and mobile clients.
- [ ] **COMMIT:** `feat(webapp): document hub mini app scaffolding`

### T5 - Docker & Compose (45-60 min)
- [x] Create docker/Dockerfile: multi-stage build, expose 8080, run uvicorn
- [x] Create docker/compose.yml: bot + qdrant services, volumes, optional ollama
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
