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
- **Phase 2: Telegram Bot & Webhooks** 🚧 **IN PROGRESS** (starting webhook endpoint)
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
- **Document Processing**: Ready for file upload and indexing pipeline
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

### ⚡ One-Command Deploy (Future)

```bash
# 1. Clone and setup
git clone https://github.com/your-username/tgrag-bot.git
cd tgrag-bot

# 2. Configure environment
cp .env.example .env
# Edit .env with your TELEGRAM_BOT_TOKEN

# 3. Launch everything
docker compose up -d --build

# 4. Verify deployment
curl http://localhost:8080/health
# Should return: {"status":"ok"}
```

### 🐳 Quick Docker Start (Current)

```bash
# Clone repository
git clone https://github.com/your-username/tgrag-bot.git
cd tgrag-bot

# Configure environment
cp .env.example .env
# Add your TELEGRAM_BOT_TOKEN to .env

# Run with Docker Compose
docker compose up --build
```

### 🏠 Local Development (Webhooks + cloudflared)

#### 1. Get Telegram Bot Token
1. Go to [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the bot token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

#### 2. Setup Environment
```bash
# Configure environment
cp .env.example .env
# Edit .env and add: TELEGRAM_BOT_TOKEN=your_token_here
```

#### 3. Run with Docker Compose
```bash
python run.py
```

**What happens automatically:**
- Docker Compose starts all services including cloudflared tunnel
- cloudflared creates temporary HTTPS domain like `https://abc123.trycloudflare.com`
- Bot automatically reads the tunnel URL from cloudflared logs
- Registers webhook: `https://abc123.trycloudflare.com/webhook/telegram`
- Bot becomes available for testing via webhooks

**Check the logs** with `docker compose logs bot` to see webhook setup confirmation!

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

# Cloudflared logs
docker compose logs cloudflared

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
- **URL mismatch**: Ensure webhook URL matches cloudflared tunnel URL
- **Network issues**: Check cloudflared connection status
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


## 🏗️ Architecture

```
tgrag-bot/
├── apps/bot/                 # Main FastAPI application
│   ├── main.py              # Application entry point & lifespan
│   ├── settings.py          # Pydantic configuration
│   ├── tg/handlers.py       # Telegram bot handlers (T3)
│   └── routes/
│       ├── health.py        # Health check endpoint
│       └── api.py           # API routes (future)
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

### Docker Services

- **bot**: FastAPI application with aiogram polling
- **qdrant**: Vector database for embeddings (ready for RAG)
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
- [x] **Project scaffolding** - Poetry, ruff, pre-commit, professional README
- [x] **FastAPI backend** - health checks, CORS, logging, static file serving
- [x] **Environment management** - Pydantic settings, webhook configuration
- [x] **Development tooling** - run.py script, proper Python path handling
- [x] **Webhook preparation** - infrastructure ready for Telegram webhooks

### Phase 2: Telegram Bot & Webhooks 🚧 IN PROGRESS
- [ ] **Webhook endpoint** - POST /webhook/telegram with aiogram integration
- [ ] **Bot commands** - /start and /menu handlers with WebApp buttons
- [ ] **Local development** - cloudflared tunneling for webhook testing
- [ ] **Ubuntu deployment** - automated server setup with HTTPS

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
- **Linting**: `ruff check .`
- **Formatting**: `ruff format .`
- **Type checking**: `mypy .` (future)
- **Tests**: `pytest` (future)

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
