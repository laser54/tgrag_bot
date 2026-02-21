# 🤖 Telegram RAG Bot

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-26A5E4?style=for-the-badge&logo=telegram)](https://aiogram.dev)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)](https://docker.com)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-FF6B35?style=for-the-badge)](https://qdrant.tech)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

> 🚀 **One-command deploy** of a Telegram bot with RAG (Retrieval-Augmented Generation) memory. Users can upload files, index them, and ask intelligent questions powered by vector search.

## ✅ Current Status
- **Phase 1: Core Infrastructure** ✅ **COMPLETED**
- **Phase 2: Telegram Bot & Webhooks** ✅ **COMPLETED** (webhook flow, commands, deploy scripts)
- **Ready for:** Local development, webhook testing, Ubuntu deployment
- **Tech Stack:** FastAPI + aiogram v3 + Qdrant + Docker

## ✨ Features

### 🤖 Telegram Integration
- **Smart Commands**: `/start` and `/menu` with welcome messages
- **Mini App**: Integrated WebApp interface accessible via inline keyboard
- **User Management**: Optional user access control via `ALLOWED_USER_IDS`
- **Real-time Communication**: Built on aiogram v3 for modern Telegram Bot API

### 🧠 RAG-Powered Intelligence
- **Vector Search**: Qdrant vector database for semantic search
- **Qdrant Cloud Ready**: Default install ships in `not_configured` mode; drop credentials into the Mini App → Vector Store panel to flip between Cloud and local Docker backends. `/api/settings/qdrant` + `/qdrant/status` expose runtime health/usage.
- **Document Processing**: Ready for file upload and indexing pipeline
- **Document APIs Today**: `/api/documents` CRUD + `/api/search` stubs keep the Mini App fully interactive while OpenAI embeddings/LLM wiring is pending.
- **Contextual Responses**: Citations and source references in answers
- **Extensible**: Modular design for adding new file formats

### 🛠️ Developer Experience
- **FastAPI Backend**: Modern async web framework with auto-generated API docs
- **Health Monitoring**: Comprehensive health checks and logging
- **Docker Ready**: Containerized deployment with docker-compose
- **Type Safety**: Full type hints with Pydantic validation
- **Code Quality**: Ruff linting and pre-commit hooks

### 📊 Production Ready
- **Scalable Architecture**: Single-process design with async operations
- **Configuration Management**: Environment-based settings with validation
- **Logging**: Structured logging with loguru
- **Error Handling**: Graceful failure handling and recovery

## 🚀 Quick Start

### Prerequisites
- ![Docker](https://img.shields.io/badge/Docker-20.10+-2496ED?style=flat&logo=docker) & Docker Compose
- ![Telegram](https://img.shields.io/badge/Telegram-Bot_Token-26A5E4?style=flat&logo=telegram) from [@BotFather](https://t.me/botfather)

### 🐳 Local Docker (Pinggy SSH tunnel)

```bash
# Clone repository
git clone https://github.com/your-username/tgrag-bot.git
cd tgrag-bot

# Configure environment
cp .env.example .env
# Add your TELEGRAM_BOT_TOKEN to .env
# (Optional) Add PINGGY_TOKEN for persistent URL

# Run local stack (bot + Pinggy tunnel, remote Qdrant optional)
docker compose up --build
```

### ☁️ Production Deployment (Ubuntu + Traefik)

Prerequisites:

- Fresh Ubuntu 22.04/24.04 VPS with public IPv4
- Outbound HTTPS + curl available (`sudo apt-get update && sudo apt-get install -y curl`)
- Domain with an A record pointing to the server
- Telegram bot token

```bash
curl -fsSL https://raw.githubusercontent.com/laser54/tgrag_bot/main/deploy/bootstrap.sh \
  | sudo bash -s -- bot.example.com 123456:ABC admin@example.com
```

Arguments: `<domain> <telegram_bot_token> [letsencrypt_email] [allowed_user_ids]`

What the script does:

- Validates OS version, DNS, and that ports 80/443 are free
- Installs Docker CE + compose plugin, git, jq, dnsutils, rsync, ufw
- Stops/disables nginx/apache and previous `tgrag-bot` systemd/docker stack
- Syncs the repo into `/opt/tgrag-bot`
- Generates `.env` + Traefik env file with HTTPS webhook URL
- Prepares `data/traefik/acme.json` for certificates (chmod 600)
- Builds & starts Traefik + bot + Qdrant via `docker-compose.prod.yml`
- Waits for bot health with progress output, registers Telegram webhook, installs systemd unit

### 🏠 Local Development (Pinggy)

#### 1. Get Telegram Bot Token
1. Go to [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the bot token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

#### 2. Setup Environment
```bash
# Configure environment
cp .env.example .env
# Edit .env and add: TELEGRAM_BOT_TOKEN=your_token_here
# (Optional) Add PINGGY_TOKEN for persistent tunnel URL (https://pinggy.io)
# (Optional) Add QDRANT_URL / QDRANT_API_KEY later, after you create a Qdrant Cloud project
```

#### 3. Run with Docker Compose
```bash
# 1. Local development with Pinggy tunnel (automatic HTTPS)
export TELEGRAM_BOT_TOKEN=your_token
# You can skip QDRANT_* vars on the very first launch
uv run run.py  # automatically starts Pinggy tunnel and configures webhooks

# 2. Production on VPS with domain
# Deploy to clean Ubuntu server with domain attached:
bash deploy/ubuntu-setup.sh yourdomain.com
# That's it! Bot will be running with HTTPS

# Local Qdrant profile (optional)
USE_LOCAL_QDRANT=1 uv run run.py
docker compose --profile local-qdrant up --build
```

**What happens automatically:**
- Docker Compose starts all services including Pinggy SSH tunnel
- Pinggy creates temporary HTTPS domain like `https://xxxxx.free.pinggy.link`
- Bot automatically reads the tunnel URL from Pinggy logs
- Registers webhook: `https://xxxxx.free.pinggy.link/webhook/telegram`
- Bot becomes available for testing via webhooks
- Vector Store panel inside the Mini App stays in `Not configured` mode until you paste Qdrant Cloud credentials (URL + API key) post-install.

**Check the logs** with `docker compose logs bot` to see webhook setup confirmation!

### 🧠 Qdrant Modes
- **Default:** the bot boots without any Qdrant credentials and waits for you to supply them later (via `.env` or secrets).
- **Remote:** when you have credentials, set `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION` (free Qdrant Cloud tier works fine).
- **Local:** set `USE_LOCAL_QDRANT=1` (or `true`) before `python run.py` or run `docker compose --profile local-qdrant up --build`.
- When local mode is off, the `qdrant` service is skipped entirely, cutting build time and resource usage.
- When local mode is on, point `QDRANT_URL` to `http://qdrant:6333` (internal Docker hostname) and leave `QDRANT_API_KEY` empty.
- Runtime changes happen through the Mini App (Vector Store card) or programmatically via `PUT /api/settings/qdrant`, so you can deploy first and configure Qdrant later.

## 🔍 Diagnostics

### Check Bot Status
```bash
curl http://localhost:8080/status
```
Returns bot initialization status, webhook configuration, and bot info.

### Check Health
```bash
curl http://localhost:8080/health
```
Returns `{"status": "ok"}` if the service is running.

### View Logs
```bash
# Bot logs
docker compose logs bot

# Pinggy tunnel logs
docker compose logs pinggy

# All logs
docker compose logs
```

### Common Issues

#### 🤖 Bot Not Responding
1. **Check token validity**: Look for `✅ Bot token is valid` in logs
2. **Check webhook setup**: Look for `✅ Webhook configured successfully` in logs
3. **Check webhook URL**: Visit `/status` endpoint to verify webhook URL
4. **Check Telegram**: Send `/start` to bot and watch webhook logs for incoming requests

#### 🌐 Webhook Issues
- **URL mismatch**: Ensure webhook URL matches Pinggy tunnel URL
- **Network issues**: Check Pinggy connection status (`docker compose logs pinggy`)
- **Telegram API**: Webhook may take time to propagate (up to 1 minute)

#### 📝 Debug Commands
```bash
# Test webhook endpoint directly
curl -X POST http://localhost:8080/webhook/telegram \
  -H "Content-Type: application/json" \
  -d '{"update_id": 1, "message": {"message_id": 1, "text": "test"}}'

# Check bot webhook info
curl http://localhost:8080/status
```

#### 6. API Documentation
When running, API docs available at: `http://localhost:8080/docs`

## 🔌 Runtime APIs (current stubs)
- `GET /health` – FastAPI health probe
- `GET /qdrant/status` – Current mode (`cloud`, `local`, `disabled`, `not_configured`), reachability, collection health, and vector counters
- `GET/PUT /api/settings/qdrant` – Read or update Qdrant URL/API key/collection (Mini App uses this for post-install credentials)
- `GET /api/documents` – List uploaded documents with metadata, index flags, and chunk counts
- `POST /api/documents` – Upload a file (metadata-only today) and queue it for future processing
- `POST /api/documents/{id}/index` – Stub indexer; validates Qdrant availability before toggling the `indexed` flag
- `POST /api/documents/{id}/remove-from-index` – Stub removal endpoint that flips `indexed=false` and clears chunk counters
- `DELETE /api/documents/{id}` – Delete stored metadata (vectors will be removed once RAG is fully wired)
- `POST /api/search` – Stub semantic search returning mocked chunks referencing uploaded docs

## 🏗️ Architecture

```
tgrag-bot/
├── apps/bot/                 # Main FastAPI application
│   ├── main.py              # Application entry point & lifespan
│   ├── settings.py          # Pydantic configuration
│   ├── documents/           # In-memory document store (dev stub)
│   ├── qdrant/              # Runtime config + status helpers
│   ├── tg/handlers.py       # Telegram bot handlers (T3)
│   └── routes/
│       ├── health.py        # Health check endpoint
│       ├── qdrant.py        # GET /qdrant/status
│       ├── settings_api.py  # Runtime settings (Qdrant etc.)
│       ├── documents.py     # Document CRUD + index/remove stubs
│       └── search.py        # POST /api/search (stubbed)
├── webapp/                  # Telegram Mini App frontend
│   ├── index.html           # Main Mini App page
│   ├── app.js              # Frontend logic
│   └── styles.css          # Mini App styling
├── docker/                  # Containerization
│   ├── Dockerfile          # Multi-stage build
│   └── compose.yml         # Services orchestration
├── data/                    # Persistent data storage
│   └── .gitkeep            # Placeholder for uploads
└── docs/                    # Documentation (future)
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token from [@BotFather](https://t.me/botfather) | ✅ | - |
| `ALLOWED_USER_IDS` | Comma-separated user IDs for access control | ❌ | All users |
| `PORT` | Server port | ❌ | `8080` |
| `WEBAPP_URL` | Mini App URL | ❌ | `http://localhost:8080/webapp/` |
| `QDRANT_URL` | Managed Qdrant Cloud endpoint (can be set later via Mini App) | ❌ | - |
| `QDRANT_API_KEY` | API key for Qdrant Cloud | ❌ | - |
| `QDRANT_COLLECTION` | Default Qdrant collection | ❌ | `tgrag-bot` |
| `USE_LOCAL_QDRANT` | `true` to run bundled qdrant service | ❌ | `false` |
| `PINGGY_TOKEN` | Token from [pinggy.io](https://pinggy.io) for persistent tunnel URL | ❌ | - |
| `OPENAI_API_KEY` | API key for OpenAI/OpenAI-compatible provider | ❌ | - |
| `OPENAI_BASE_URL` | Base URL for OpenAI-compatible APIs (Azure, Ollama, etc.) | ❌ | - |
| `EMBEDDING_MODEL` | Embedding model name | ❌ | `text-embedding-3-large` |
| `LLM_MODEL` | Chat/answering model | ❌ | `gpt-5.1-mini` |
| `UPLOAD_DIR` | Directory for uploaded documents | ❌ | `data/uploads` |
| `MAX_FILE_SIZE_MB` | Maximum file upload size in MB | ❌ | `10` |

> **Note on models (Jan 2026):** GPT-4o is deprecated (sunset Feb 2026). Default LLM is now `gpt-5.1-mini`. For embeddings, `text-embedding-3-large` provides best quality. `QDRANT_*` and `OPENAI_*` vars are optional — configure via Mini App after deployment.


### Docker Services

- **bot**: FastAPI application with aiogram webhooks
- **pinggy**: SSH tunnel for HTTPS webhook URL (local dev only)
- **qdrant**: Vector database (enabled only with `local-qdrant` profile)
- **ollama**: Local LLM server (optional, commented out)

## 🛠️ Tech Stack

### Backend
- **Framework**: ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi) - Modern async web framework
- **Bot Framework**: ![aiogram](https://img.shields.io/badge/aiogram-3.x-26A5E4?style=flat&logo=telegram) - Telegram Bot API framework
- **Validation**: ![Pydantic](https://img.shields.io/badge/Pydantic-2.x-E92063?style=flat&logo=pydantic) - Data validation
- **Database**: ![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-FF6B35?style=flat) - Vector similarity search

### DevOps & Quality
- **Container**: ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker) - Containerization
- **Linting**: ![Ruff](https://img.shields.io/badge/Ruff-FCC624?style=flat&logo=ruff) - Fast Python linter
- **Formatting**: ![Black](https://img.shields.io/badge/Black-000000?style=flat&logo=black) - Code formatting
- **Hooks**: ![pre-commit](https://img.shields.io/badge/pre--commit-FAB040?style=flat&logo=pre-commit) - Git hooks

### Frontend (Mini App)
- **HTML5** with Telegram WebApp SDK
- **Vanilla JavaScript** for interactivity
- **CSS3** with mobile-first responsive design

## 📈 Roadmap

### Phase 1: Core Infrastructure ✅ COMPLETED
- [x] **Project scaffolding** - uv, ruff, pre-commit, professional README
- [x] **FastAPI backend** - health checks, CORS, logging, static file serving
- [x] **Environment management** - Pydantic settings, webhook configuration
- [x] **Development tooling** - run.py script, proper Python path handling
- [x] **Webhook preparation** - infrastructure ready for Telegram webhooks

### Phase 2: Telegram Bot & Webhooks ✅ COMPLETED
- [x] **Webhook endpoint** - POST /webhook/telegram powered by aiogram
- [x] **Bot commands** - /start and /menu with WebApp button
- [x] **Local development** - Pinggy SSH tunnel for webhook testing
- [x] **Ubuntu deployment** - Traefik-based automated Docker script

### Phase 3: RAG Implementation 📋
- [ ] **File upload API** - validation and processing pipeline
- [ ] **Document processing** - PDF, DOCX, TXT format support
- [ ] **Vector embeddings** - integration with Ollama or OpenAI
- [ ] **Semantic search** - Qdrant-powered similarity search
- [ ] **Contextual Q&A** - citations and source references

### Phase 4: Advanced Features 🚀
- [ ] **Multi-format support** - images, audio, video processing
- [ ] **Conversation memory** - chat history and context retention
- [ ] **User management** - admin panel and access controls
- [ ] **Analytics dashboard** - usage metrics and insights
- [ ] **Multi-language** - internationalization support

### Phase 5: Production Polish 🎯
- [ ] **Error handling** - comprehensive exception management
- [ ] **Security hardening** - rate limiting, input validation
- [ ] **Monitoring & logging** - centralized observability
- [ ] **CI/CD pipeline** - automated testing and deployment
- [ ] **Performance optimization** - caching, async processing

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Fork and clone
git clone https://github.com/your-username/tgrag-bot.git
cd tgrag-bot

# Setup pre-commit hooks
pre-commit install

# Create feature branch
git checkout -b feature/amazing-feature
```

### Code Quality
- **Linting**: `uv run ruff check .`
- **Formatting**: `uv run ruff format .`
- **Type checking**: `uv run mypy .` (future)
- **Tests**: `uv run pytest` (future)

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com) - The modern async web framework
- [aiogram](https://aiogram.dev) - Powerful Telegram Bot framework
- [Qdrant](https://qdrant.tech) - Vector database for AI applications
- [Telegram](https://telegram.org) - The best messaging platform

---

<p align="center">
  <b>Built with ❤️ for the Telegram and AI communities</b><br>
  <sub>Star this repo if you find it useful! ⭐</sub>
</p>
