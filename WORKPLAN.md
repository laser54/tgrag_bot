# Telegram RAG Bot - Work Plan

## Overview
One-command deploy (Docker) of a Telegram bot with RAG memory. Users can drop files, index them, and ask questions.

**Principles:** Simplicity > features, sane defaults, no GPU, works on Linux/x86_64 and Apple Silicon.

**Stack:** Python 3.12, aiogram v3 + FastAPI, Qdrant (vector DB), LlamaIndex (RAG framework), Ollama optional.

**Current Status:** ✅ T1-T3.3 delivered. ✅ Docker packaging in place. 🚧 Telegram Mini App UX & wiring underway. ⏳ Documentation polish pending.

## Project Structure
```
tgrag-bot/
├─ apps/bot/
│  ├─ main.py              # FastAPI + aiogram integration
│  ├─ settings.py          # Pydantic BaseSettings, env validation
│  ├─ documents/           # In-memory store for uploaded docs (dev stub)
│  ├─ qdrant/              # Runtime config + status helpers
│  ├─ rag/                 # LlamaIndex RAG services (T10)
│  ├─ tg/handlers.py       # /start, /menu
│  └─ routes/
│      ├─ health.py        # GET /health
│      ├─ qdrant.py        # GET /qdrant/status
│      ├─ settings_api.py  # GET/PUT runtime settings (Qdrant etc.)
│      ├─ documents.py     # CRUD + index/remove document stubs
│      ├─ search.py        # POST /api/search (stubbed)
│      └─ chat.py          # POST /api/chat (T10.4)
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
- [x] Add `local-qdrant` profile + remote Qdrant Cloud env wiring
- [ ] **TEST:** docker compose up -d --build, curl localhost:8080/health returns ok
- [ ] **COMMIT:** `chore(docker): Dockerfile and compose with qdrant`

### T6 - Docs Polish & Guardrails (30-45 min)
- [ ] Expand README: Quickstart (Docker, local run), Troubleshooting, Roadmap
- [ ] Add Makefile with make dev, make up, make down
- [ ] Ensure pre-commit install instructions
- [ ] **TEST:** Follow README instructions to verify setup works
- [ ] **COMMIT:** `docs: quickstart, troubleshooting, roadmap`

### T7 - Qdrant Cloud Integration ✅ COMPLETED (0.5 day)
- [x] Extend `settings.py` with `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION`, `USE_LOCAL_QDRANT`, defaulting to a safe `not_configured` mode.
- [x] Add runtime config store + `/qdrant/status` endpoint to report mode, reachability, collection existence, and usage counters without leaking secrets.
- [x] Expose `/api/settings/qdrant` (GET/PUT) so operators enter Qdrant Cloud credentials after deployment via the Mini App instead of baking them into `.env`.
- [x] Build Mini App panel for mode switching (cloud/local/disabled), credential entry, and live status/metrics with toast feedback.
- [x] Document the post-install workflow: deploy first, then open the WebApp → Vector Store card → paste Qdrant Cloud URL/key to go live.

### T8 - Document Ingestion Pipeline 🚧 IN PROGRESS (~1 day)
- [x] Implement thread-safe in-memory `DocumentStore` with upload timestamps, sizes, indexing flags, and chunk counters.
- [x] Ship `/api/documents` CRUD endpoints plus indexing/removal stubs that guard on Qdrant availability and keep the Mini App optimistic UI in sync.
- [ ] Persist uploads to disk/object storage (beyond metadata) for future processing workers.
- [ ] ~~Implement file chunking/tokenization strategy per format (PDF/DOCX/TXT/Markdown) with overlap and metadata payloads for Qdrant.~~ → Moved to T10 with LlamaIndex.
- [ ] ~~Invoke OpenAI embedding API + Qdrant upserts/deletes as soon as credentials are available.~~ → Moved to T10 with LlamaIndex.
- [ ] **TEST:** Upload → index → reindex → delete flows visible both in the Mini App and API logs.

### T9 - Semantic Search API 🚧 PLANNED (0.5 day)
- [x] Add `/api/search` stub that returns mocked chunks referencing current documents to unblock UX wiring.
- [ ] ~~Replace stub with real Qdrant similarity search once embeddings/Qdrant writes are enabled.~~ → Moved to T10 with LlamaIndex query engine.
- [ ] Support filters (document IDs/tags) and pagination to keep the API future-proof.
- [ ] Document response schema for downstream chat/answering endpoint integration.

### T10 - LlamaIndex RAG Integration 🚧 PLANNED (~3 days)
**Goal:** Integrate LlamaIndex as the core RAG framework, leveraging Qdrant for vector storage. Replace manual chunking/embeddings with LlamaIndex's high-level APIs for document ingestion, indexing, and retrieval.

**Architecture:**
```
apps/bot/rag/
├── __init__.py          # Lazy singleton RAGService
├── service.py           # RAGService: init, query, index, delete
├── indexer.py           # DocumentIndexer with LlamaIndex
├── retriever.py         # QueryEngine wrapper with filters
└── models.py            # Pydantic schemas for RAG responses
```

**Models (as of Jan 2026):**
- Embedding: `text-embedding-3-large` (OpenAI)
- LLM: `gpt-5.1-mini` (replaces deprecated gpt-4o, sunset Feb 2026)
- Alternative: Ollama for local inference

#### T10.0 - Foundation & File Persistence (0.5 day) ⭐ NEW
- [x] Add OpenAI/LLM settings to `settings.py`: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `EMBEDDING_MODEL`, `LLM_MODEL`
- [x] Add document storage settings: `UPLOAD_DIR`, `MAX_FILE_SIZE_MB`
- [x] Update `.env.example` with new variables
- [x] Implement file persistence in `/api/documents` upload: save to `data/uploads/{doc_id}_{filename}`
- [x] Add SQLite or JSON file for document metadata persistence (survives container restart)
- [x] **TEST:** Upload file → restart container → file and metadata still exist


#### T10.1 - LlamaIndex Setup & Dependencies (0.5 day)
- [x] Add LlamaIndex core, vector-stores-qdrant, embeddings-openai to pyproject.toml.
- [ ] Update Docker build to include new deps (ensure compatibility with existing Qdrant client).
- [ ] Create `apps/bot/rag/` module structure with lazy initialization pattern.
- [ ] Implement `RAGService` singleton with connection reuse and health checks.
- [ ] Initialize LlamaIndex with Qdrant vector store, using existing config from `qdrant/config_store.py`.
- [ ] Add graceful degradation when OpenAI API key is missing (return helpful error, not crash).
- [ ] **TEST:** Basic LlamaIndex + Qdrant connection works, can create empty index.

#### T10.2 - Document Ingestion with LlamaIndex (0.75 day)
- [ ] Replace manual chunking in T8 with LlamaIndex `SimpleDirectoryReader` + `SentenceSplitter` for supported formats (PDF, DOCX, TXT, Markdown).
- [ ] Implement `DocumentIndexer.add_document(file_path, metadata)` using LlamaIndex's `VectorStoreIndex.from_documents()` with Qdrant as backend.
- [ ] Update `/api/documents/{id}/index` endpoint to:
  - Call LlamaIndex ingestion with real embeddings
  - Track actual chunk counts from LlamaIndex
  - Store node IDs for later deletion
- [ ] Handle reindexing: remove old nodes by `doc_id` metadata filter, re-add with updated content.
- [ ] Add error handling for unsupported formats or embedding failures (return 400 with details).
- [ ] Implement background indexing with status polling (optional, for large files).
- [ ] **TEST:** Upload document → index → verify vectors in Qdrant collection with correct metadata.

#### T10.3 - Semantic Search with LlamaIndex Query Engine (0.5 day)
- [ ] Update `/api/search` to use LlamaIndex `VectorIndexRetriever` with similarity search over Qdrant.
- [ ] Support filters: document IDs via metadata, pagination (limit/offset).
- [ ] Return structured response: chunks with scores, source document metadata, highlighted snippets.
- [ ] Integrate with existing Qdrant config checks (reachable, collection exists).
- [ ] Add embedding caching for repeated queries (optional).
- [ ] **TEST:** Search query returns relevant chunks from indexed documents with correct scores.

#### T10.4 - Chat/Answer Endpoint (0.5 day)
- [ ] Add `/api/chat` POST endpoint for RAG-powered Q&A.
- [ ] Use LlamaIndex `QueryEngine` with response synthesis.
- [ ] Accept: `query`, optional `document_ids` filter, optional `conversation_id` for context.
- [ ] Return: `answer`, `sources[]` with document names and page references.
- [ ] Add streaming response option (`/api/chat/stream`) for long answers.
- [ ] **TEST:** Ask question via API, get answer citing indexed docs.

#### T10.5 - Telegram Bot Integration (0.5 day) ⭐ NEW
- [ ] Refactor `tg/handlers.py` to use `RAGService` for incoming messages.
- [ ] Check RAG readiness (OpenAI + Qdrant configured) before processing.
- [ ] If not ready: reply with setup instructions and Mini App link.
- [ ] If ready: query RAG and return answer with source citations.
- [ ] Add typing indicator while processing (show "bot is typing...").
- [ ] Handle errors gracefully: timeout, API errors, empty results.
- [ ] Support `/ask <question>` command as explicit RAG query.
- [ ] **TEST:** Send message to bot → get RAG-powered response with sources.

#### T10.6 - Performance & Reliability (0.25 day) ⭐ NEW
- [ ] Use `AsyncQdrantClient` for non-blocking vector operations.
- [ ] Add connection pooling for OpenAI API (httpx limits).
- [ ] Implement retry with exponential backoff for embedding requests.
- [ ] Add request timeout configuration (default 30s for embeddings, 60s for LLM).
- [ ] Log latency metrics for indexing and query operations.
- [ ] **TEST:** Concurrent requests don't cause connection errors.



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
# You can skip QDRANT_* vars on the very first launch
python run.py  # automatically starts cloudflared and configures webhooks

# 2. Production on VPS with domain
# Deploy to clean Ubuntu server with domain attached:
bash deploy/ubuntu-setup.sh yourdomain.com
# That's it! Bot will be running with HTTPS

# Local Qdrant profile (optional)
USE_LOCAL_QDRANT=1 python run.py
docker compose --profile local-qdrant up --build

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
- **RAG stubs only:** Document + search APIs exist but still use mocked embeddings until OpenAI wiring ships
- **Clean logs:** Structured INFO on start, WARN on missing config
- **Security:** Don't log tokens, restrict /menu to private chats
- **Simple deployment:** 2-3 commands setup on clean Ubuntu server
- **Qdrant Cloud first:** Managed Qdrant (free tier) by default, local qdrant only when `USE_LOCAL_QDRANT=true`
- **Post-install Qdrant config:** Default install ships with `not_configured` mode; operators paste Cloud credentials inside the Mini App when ready
- **LlamaIndex for RAG:** Use LlamaIndex framework for document processing, embeddings, and retrieval over Qdrant to simplify implementation and ensure best practices
