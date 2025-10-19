# Telegram RAG Bot - Work Plan

## Overview
One-command deploy (Docker) of a Telegram bot with RAG memory. Users can drop files, index them, and ask questions.

**Principles:** Simplicity > features, sane defaults, no GPU, works on Linux/x86_64 and Apple Silicon.

**Stack:** Python 3.12, aiogram v3 + FastAPI, Qdrant (vector DB), Ollama optional.

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

### T1 - Repo Hygiene (30-45 min)
- [x] Add MIT LICENSE
- [x] Add .gitignore (Python, Node, Docker)
- [x] Add .editorconfig
- [x] Add ruff.toml (reasonable defaults)
- [x] Add .pre-commit-config.yaml (ruff + trailing-whitespace + end-of-file-fixer)
- [x] Initialize Poetry/venv with dependencies
- [x] Create .env.example with required vars
- [x] Add basic README scaffold
- [ ] **TEST:** Install pre-commit hooks and run
- [ ] **COMMIT:** `chore: scaffold repo, tooling, env example`

### T2 - FastAPI Application + Health Route (30 min)
- [ ] Create apps/bot/main.py: FastAPI app, mount static /webapp/*, include router
- [ ] Create routes/health.py: GET /health returns {"status":"ok"}
- [ ] Create settings.py: Pydantic BaseSettings with env validation (TELEGRAM_BOT_TOKEN required)
- [ ] **TEST:** Run server locally, curl /health returns ok
- [ ] **COMMIT:** `feat(api): FastAPI app with /health and static webapp`

### T3 - Minimal Telegram Bot (60-90 min)
- [ ] Create tg/handlers.py: /start and /menu handlers
- [ ] /start: short welcome + repo link
- [ ] /menu: WebApp keyboard with WebAppInfo(url=WEBAPP_URL)
- [ ] Wire aiogram polling in FastAPI lifespan/background task
- [ ] Respect ALLOWED_USER_IDS (optional filtering)
- [ ] Add logging for startup/errors
- [ ] **TEST:** Run with test token, verify /start and /menu responses
- [ ] **COMMIT:** `feat(bot): minimal aiogram bot with /start and /menu`

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
- [ ] Fresh clone → .env filled → docker compose up -d --build
- [ ] GET /health returns {"status":"ok"}
- [ ] Telegram bot answers /start and shows working WebApp button on /menu
- [ ] README explains this flow

## Testing Strategy
- After T1: pre-commit hooks work, basic linting passes
- After T2: health endpoint responds correctly
- After T3: bot responds to commands, WebApp button appears
- After T4: Mini App loads and shows health status
- After T5: Docker containers start successfully
- After T6: Complete end-to-end verification

## Commands Reference
```bash
# Setup
pre-commit install || true
pip install -r requirements.txt  # fallback if poetry fails

# Local run
export TELEGRAM_BOT_TOKEN=123:abc
uvicorn apps.bot.main:app --reload --port 8080

# Docker
docker compose up -d --build
curl http://localhost:8080/health
```

## Constraints & Guardrails
- No webhook today: use polling for simplicity
- Fail fast on env: exit with clear message if TELEGRAM_BOT_TOKEN missing
- No RAG yet: Qdrant runs but unused
- Clean logs: structured INFO on start, WARN on missing config
- Security: don't log tokens, restrict /menu to private chats
