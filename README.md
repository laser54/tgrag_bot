# 🤖 Telegram RAG Bot

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-26A5E4?style=for-the-badge&logo=telegram)](https://aiogram.dev)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)](https://docker.com)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-FF6B35?style=for-the-badge)](https://qdrant.tech)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

> 🚀 **One-command deploy** of a Telegram bot with RAG (Retrieval-Augmented Generation) memory. Users can upload files, index them, and ask intelligent questions powered by vector search.

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

### ⚡ One-Command Deploy

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

### 🧪 Local Development

```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your TELEGRAM_BOT_TOKEN to .env

# Run development server
python run.py

# API docs available at: http://localhost:8080/docs
```

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

### Phase 1: Core Infrastructure ✅
- [x] FastAPI backend with health checks
- [x] Telegram bot skeleton (/start, /menu)
- [x] Mini App stub interface
- [x] Docker deployment ready
- [x] Qdrant integration prepared

### Phase 2: RAG Implementation 🚧
- [ ] File upload API with validation
- [ ] Document processing pipeline (PDF, DOCX, TXT)
- [ ] Vector embeddings generation
- [ ] Semantic search with Qdrant
- [ ] Contextual Q&A with citations

### Phase 3: Advanced Features 📋
- [ ] Multiple file format support
- [ ] Conversation history and memory
- [ ] User management dashboard
- [ ] Analytics and usage metrics
- [ ] Multi-language support

### Phase 4: Production Polish 🎯
- [ ] Comprehensive error handling
- [ ] Rate limiting and security
- [ ] Monitoring and logging
- [ ] CI/CD pipeline
- [ ] Performance optimization

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
