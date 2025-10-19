# Telegram RAG Bot

One-command deploy (Docker) of a Telegram bot with RAG memory. Users can drop files, index them, and ask questions.

## Features
- Telegram bot with /start and /menu commands
- WebApp Mini App interface
- Health check endpoint
- Docker Compose deployment
- Qdrant vector database integration (ready for RAG)

## Quickstart

### Prerequisites
- Docker and Docker Compose
- Telegram Bot Token (get from [@BotFather](https://t.me/botfather))

### Setup
1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your values
3. Run with Docker Compose:
   ```bash
   docker compose up -d --build
   ```
4. Check health: `curl http://localhost:8080/health`

### Environment Variables
- `TELEGRAM_BOT_TOKEN`: Your bot token from BotFather (required)
- `ALLOWED_USER_IDS`: Comma-separated list of allowed user IDs (optional)
- `PORT`: Server port (default: 8080)
- `WEBAPP_URL`: WebApp URL (default: http://localhost:8080/webapp/)

## Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
export TELEGRAM_BOT_TOKEN=your_token
uvicorn apps.bot.main:app --reload --port 8080
```

## Project Structure
```
tgrag-bot/
├─ apps/bot/          # Main application
├─ webapp/            # Mini App frontend
├─ docker/            # Docker configuration
├─ data/              # Data directory
└─ docs/              # Documentation
```

## Roadmap
- [ ] File upload and indexing
- [ ] RAG chat with citations
- [ ] Multiple file format support
- [ ] User management
- [ ] Advanced search features
