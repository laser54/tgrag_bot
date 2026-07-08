# tgrag_bot — Active Execution Roadmap

> Single source of truth for the next agent. Do the tasks **in the order below**.
> Each task lists: goal, files to touch, concrete steps, and **binding acceptance criteria**.
> A task is "done" only when every checkbox under "Acceptance" is verified (command output or test run), not just written.
>
> Companion docs:
> - [WORKPLAN.md](WORKPLAN.md) — long-term swarm architecture & phase history (Phases 1-3 already done).
> - [README.md](README.md) — runtime, APIs, deploy.

## TL;DR — where to start

The multi-bot skeleton (dynamic webhook, `BotRegistry`, admin provisioning) is done. **The RAG core is entirely stubbed** and **Telegram is stuck on Bot API 9.6** while 10.1 (Rich Messages + reply streaming) is out. Two parallel tracks, both pragmatic (no over-engineering):

- Track 1 (data + security): tasks **A1 -> A2 -> A3**
- Track 2 (RAG core + modern Telegram UX): tasks **B1 -> B2 -> B3 -> C1 -> C2 -> C3**
- Track 3 (polish): tasks **D1 -> D2 -> D3**

Recommended global order: `A1, A2, B1, B2, C1, B3, C2, C3, A3, D1, D2, D3`.

## Ground rules (do not break these)

- Async-first, typed (Pydantic + typed SQLAlchemy). No blocking I/O in the webhook/request path.
- Dependencies via `uv` only (`uv add ...`, then commit `uv.lock`).
- English for all code/comments/docs. Run `uv run ruff check .` and `uv run ruff format .` before every commit.
- Backward compatible: do not remove legacy `POST /webhook/telegram` or JSON store until the replacing task's acceptance passes.
- Never leak across tenants: **every** Qdrant read/write MUST carry a `bot_id` filter/payload. Centralize filter construction so it is impossible to query without it.
- Do not commit unless explicitly asked. Keep changes scoped per task.

## Current stub inventory (what is fake today)

- Indexing: [apps/bot/routes/documents.py](apps/bot/routes/documents.py) uses `chunk_guess = size / 2000`. No parse/chunk/embed/upsert.
- Search: [apps/bot/routes/search.py](apps/bot/routes/search.py) returns mock chunks with `status="stubbed"`.
- Telegram Q&A: catch-all in [apps/bot/tg/handlers/user.py](apps/bot/tg/handlers/user.py) echoes "Soon there will be RAG logic". LLM never called.
- Storage split: documents live in JSON ([apps/bot/documents/store.py](apps/bot/documents/store.py)); ORM `Document` in [apps/bot/db/models.py](apps/bot/db/models.py) is unused by the API.
- No Alembic (`Base.metadata.create_all` on startup in [apps/bot/db/engine.py](apps/bot/db/engine.py)).
- Security gaps: webhook secret not validated; Mini App `initData` not validated; `/api/*` open.
- `llama-index` + `openai` are in `pyproject.toml` but have **0 imports** in code.

---

# Track 1 — Data layer & security

## A1. Alembic + DocumentsRepository + kill JSON dual storage

**Goal:** durable, single-source document state in SQLite; migrations instead of `create_all`.

**Files:** `apps/bot/db/repositories/documents.py` (new), `apps/bot/db/migrations/` (new, Alembic), `alembic.ini` (new), [apps/bot/db/engine.py](apps/bot/db/engine.py), [apps/bot/routes/documents.py](apps/bot/routes/documents.py), remove usage of [apps/bot/documents/store.py](apps/bot/documents/store.py).

**Steps:**
1. `uv add alembic`. Init Alembic against async engine; configure `sqlalchemy.url` from `DATABASE_URL`.
2. Autogenerate baseline migration from existing `Bot` + `Document` models. Add columns `Document` needs for RAG: `chunk_count int default 0`, `error text nullable`, `indexed_at datetime nullable`.
3. Replace `create_all` on startup with "run migrations to head" (or gate `create_all` behind a dev flag).
4. Add `DocumentsRepository` (list/get/create/update_status/delete) mirroring `BotsRepository` style.
5. Rewrite `routes/documents.py` to use `DocumentsRepository`. Keep response schema stable for the Mini App.
6. Delete JSON writes; keep [apps/bot/documents/store.py](apps/bot/documents/store.py) only if still read by a migration path, otherwise remove.

**Acceptance:**
- [x] `uv run alembic upgrade head` creates/updates `data/app.db` with no error on a fresh DB.
- [x] `uv run alembic downgrade -1 && uv run alembic upgrade head` round-trips cleanly.
- [x] `GET /api/documents` returns data sourced from SQLite (verify by inserting a row via repo, not JSON).
- [x] No code path writes to `documents.json` anymore (grep shows JSON store only in removed/legacy).
- [x] App starts without calling `create_all` (or only under an explicit dev flag).
- [x] `uv run ruff check .` clean.

> **Status: DONE.** Notes for the next agent:
> - Alembic config at `alembic.ini` (root); migrations under `apps/bot/db/migrations/`. Baseline revision `98b1dd9da74b` matches the models (incl. new `Document.size`, `chunk_count`, `error`, `indexed_at`).
> - `apps/bot/db/migrations/env.py` reads `DATABASE_URL` from env directly (NOT `apps.bot.settings`) so migrations run in CI without `TELEGRAM_BOT_TOKEN`.
> - `init_db` now runs `alembic upgrade head` in a worker thread (env.py owns its own event loop). `DEV_CREATE_ALL=true` is an emergency fallback only.
> - `Document.bot_id` is temporarily **nullable** (no auth yet — A2 provides bot context, B1 enforces non-null at vector-write time). No leak risk today: no vectors exist yet.
> - `routes/documents.py` keeps the Mini App contract: `id` is exposed as `str(int)`, `indexed` is derived from `status==ready`, `chunks` from `chunk_count`.
> - `routes/search.py` still reads the JSON store (read-only, stub) — replaced in B2. `apps/bot/documents/store.py` is intentionally kept until B2 per the ground rule.
> - For an **existing** `data/app.db` created by the old `create_all`, run `uv run alembic stamp head` once before starting the app (so Alembic knows the baseline is already applied).

## A2. Webhook secret + Mini App initData auth

**Goal:** reject forged webhook calls and unauthenticated Mini App API calls.

**Files:** [apps/bot/routes/webhook.py](apps/bot/routes/webhook.py), [apps/bot/main.py](apps/bot/main.py) (legacy webhook + `set_webhook`), [apps/bot/tg/handlers/common.py](apps/bot/tg/handlers/common.py) (webhook registration), new `apps/bot/security/telegram_auth.py`, [apps/bot/settings.py](apps/bot/settings.py), all `apps/bot/routes/*` under `/api`.

**Steps:**
1. Add `WEBHOOK_SECRET` setting (auto-generate per bot or one global). Pass `secret_token=` on every `set_webhook`.
2. In both webhook handlers, compare `X-Telegram-Bot-Api-Secret-Token` header using `hmac.compare_digest`; return 401/403 on mismatch.
3. Implement `validate_init_data(init_data, bot_token) -> user` (HMAC-SHA256 per Telegram WebApp spec, `hmac.compare_digest`, check `auth_date` freshness).
4. FastAPI dependency `require_tg_user` that reads `Authorization: tma <initData>`; apply to `/api/documents*`, `/api/search`, `/api/settings/*`, `/api/bots`.
5. Add a dev bypass flag (`DISABLE_WEBAPP_AUTH=true`) for local testing only, default off.

**Acceptance:**
- [ ] Webhook call without/with wrong secret header -> 401/403; with correct secret -> 200 and dispatch.
- [ ] `set_webhook` (dynamic + legacy) registers with a secret token (verify via `getWebhookInfo` or logged args).
- [ ] `/api/documents` without `Authorization: tma` -> 401; with valid initData -> 200.
- [ ] Tampered initData (modified field, kept old hash) -> 401.
- [ ] `uv run ruff check .` clean.

## A3. Conversation history model (LLM context)

**Goal:** persist per-user/per-bot dialog turns for multi-turn context.

**Files:** [apps/bot/db/models.py](apps/bot/db/models.py), Alembic migration, `apps/bot/db/repositories/conversations.py` (new).

**Steps:**
1. Add `Conversation(id, bot_id FK, chat_id, created_at)` and `Message(id, conversation_id FK, role[user|assistant|system], content, created_at)`.
2. Migration via Alembic.
3. Repository: `get_or_create_conversation(bot_id, chat_id)`, `append(role, content)`, `recent(limit)`.

**Acceptance:**
- [ ] Migration applies; tables exist.
- [ ] Repo round-trips messages; `recent(n)` returns last n in order.
- [ ] Wired into C2 handler (last N turns fed to the LLM).

---

# Track 2 — RAG core + modern Telegram (Bot API 10.1)

## B1. Ingestion pipeline (parse -> chunk -> embed -> upsert)

**Goal:** real indexing with mandatory `bot_id` isolation, off the request path.

**Files:** `apps/bot/rag/__init__.py`, `apps/bot/rag/ingestion.py` (new), `apps/bot/rag/tenancy.py` (new — the single place that builds `bot_id` payload/filter), [apps/bot/routes/documents.py](apps/bot/routes/documents.py), [apps/bot/qdrant/client.py](apps/bot/qdrant/client.py).

**Steps:**
1. Use LlamaIndex to load + chunk uploaded files (start with pdf/txt/md/docx). Config chunk size/overlap in settings.
2. Embed with `EMBEDDING_MODEL` via `llama-index-embeddings-openai`.
3. Ensure Qdrant collection exists with correct vector size/distance (create on first use).
4. Upsert vectors with payload `{bot_id (required), doc_id, filename, chunk_index, text, source}`.
5. `tenancy.py`: `payload_for(bot_id, ...)` and `filter_for(bot_id)` — the ONLY way to build payload/filter.
6. Trigger indexing from `POST /api/documents/{id}/index` as a background task (`asyncio.create_task` / `BackgroundTasks`), not inline. Update status `queued -> processing -> ready/failed` with `error` on failure.

**Acceptance:**
- [ ] Uploading + indexing a real small PDF/txt produces >0 vectors in Qdrant (verify via `/qdrant/status` count or client).
- [ ] Every upserted point payload contains a non-null `bot_id` (assert in a test).
- [ ] Document status transitions `queued -> processing -> ready`; a forced failure sets `failed` + `error`.
- [ ] Indexing does not block the HTTP response (endpoint returns immediately with `processing`).
- [ ] `uv run ruff check .` clean.

## B2. Retrieval with mandatory tenant filter

**Goal:** real semantic search isolated by `bot_id`; kill the search stub.

**Files:** `apps/bot/rag/retrieval.py` (new), [apps/bot/routes/search.py](apps/bot/routes/search.py), `apps/bot/rag/tenancy.py`.

**Steps:**
1. `retrieve(bot_id, query, top_k) -> list[Chunk]`: embed query, Qdrant search with `filter_for(bot_id)`, return scored chunks with source metadata.
2. Rewrite `routes/search.py` to call `retrieve` for the caller's `bot_id`; remove mocked `status="stubbed"`.
3. Add Qdrant + OpenAI reachability to `/status`.

**Acceptance:**
- [ ] `POST /api/search` returns real scored chunks from Qdrant (no `stubbed`).
- [ ] **Tenant isolation test:** index docs for bot A and bot B; a query as bot A never returns bot B chunks. This is a required automated test (see D3).
- [ ] Retrieval with an empty/unknown `bot_id` is rejected (cannot run unfiltered).
- [ ] `uv run ruff check .` clean.

## B3. Simple bot_type router (no full LangGraph yet)

**Goal:** dispatch behavior by `bot_type` with a plain function router; leave a clean seam for future LangGraph.

**Files:** `apps/bot/agents/__init__.py`, `apps/bot/agents/router.py` (new), `apps/bot/agents/base.py` (typed `AgentInput`/`AgentOutput`).

**Steps:**
1. Define `AgentInput(bot_id, bot_type, chat_id, query, history)` and `AgentOutput(text, citations, thinking?)`.
2. `route(input) -> AgentOutput`: `rag` = retrieve+answer (C2); `researcher`/`mentor` = same pipeline with different system prompts for now.
3. Do NOT add `langgraph` dependency yet. Document the extension point in code + WORKPLAN Phase 4.

**Acceptance:**
- [ ] All three `bot_type` values run without error and produce distinct system-prompt behavior.
- [ ] No `langgraph` import/dependency added.
- [ ] `uv run ruff check .` clean.

## C1. Upgrade aiogram to Bot API 10.1

**Goal:** unlock Rich Messages + reply streaming APIs.

**Files:** [pyproject.toml](pyproject.toml), `uv.lock`.

**Steps:**
1. `uv add "aiogram>=3.29.1"`; run `uv lock`.
2. Smoke-check the app still starts, existing handlers still register, webhook still processes an update.
3. Note: Rich Messages / `RichBlockThinking` are new — verify the exact type/method names in installed aiogram (`InputRichMessage`, `answer_rich`, `send_rich_message_draft`) before using in C3.

**Acceptance:**
- [ ] `uv.lock` shows `aiogram 3.29.1+`.
- [ ] App boots; sending `/start` to the manager bot still replies (no regression).
- [ ] `uv run ruff check .` clean.

## C2. Wire LLM answering into Telegram (replace catch-all stub)

**Goal:** the bot actually answers questions from indexed docs.

**Files:** [apps/bot/tg/handlers/user.py](apps/bot/tg/handlers/user.py), new `apps/bot/rag/answer.py`, `apps/bot/agents/router.py`, conversations repo (A3).

**Steps:**
1. `answer(bot_id, query, history) -> AgentOutput`: retrieve (B2) -> build prompt with context + citations -> call `LLM_MODEL` via OpenAI client -> return text + source citations.
2. Replace the catch-all: resolve `bot_id`/`bot_type` for the incoming update, load recent history (A3), call `route`, persist turn, reply.
3. Plain-text reply first (Rich formatting comes in C3). Handle "no relevant context" gracefully.

**Acceptance:**
- [ ] Sending a question about an indexed doc returns a grounded answer referencing the source.
- [ ] Multi-turn: a follow-up ("and what about X?") uses prior context.
- [ ] Errors (LLM/Qdrant down) reply with a friendly message, logged with `bot_id`/`update_id`, no crash.
- [ ] `uv run ruff check .` clean.

## C3. Streaming + Rich Messages (Bot API 10.1)

**Goal:** ChatGPT-like typing + structured answers with source footnotes.

**Files:** [apps/bot/tg/handlers/user.py](apps/bot/tg/handlers/user.py), `apps/bot/tg/rich.py` (new — builds `InputRichMessage`).

**Steps:**
1. Stream LLM tokens; during generation call `send_rich_message_draft` (or `sendMessageDraft`) to show progress (~30s draft window).
2. Final answer via `send_rich_message` / `answer_rich` using `InputRichMessage` (HTML or markdown).
3. Render **source citations as footnotes** (`RichBlockFooter` / `RichTextReference`) instead of inline text.
4. Optional (behind a setting): show retrieval/reasoning step via `RichBlockThinking`.
5. **Fallback:** if the chat/client rejects Rich Messages, fall back to plain `message.answer(...)`. Never fail the reply because of formatting.

**Acceptance:**
- [ ] Long answers visibly stream (draft updates) before the final message.
- [ ] Final message renders with footnote-style citations for the retrieved sources.
- [ ] Rich-message send failure falls back to plain text (simulate by forcing an error).
- [ ] `uv run ruff check .` clean.

---

# Track 3 — Mini App & quality

## D1. Mini App auth + native theme + UX

**Files:** [webapp/app.js](webapp/app.js), [webapp/styles.css](webapp/styles.css), [webapp/index.html](webapp/index.html).

**Steps:**
1. Send `Authorization: tma <tg.initData>` on every `fetchJson` (pairs with A2).
2. Apply Telegram `themeParams` to CSS variables (currently `tg-dark`/`tg-light` classes have no CSS rules); use `MainButton` for primary actions, add `HapticFeedback`.
3. Wire the still-stubbed System Prompt and Model Router panels to real endpoints (add endpoints if missing).

**Acceptance:**
- [ ] Mini App works only with valid initData (calls succeed in Telegram, 401 when opened raw in a browser without auth bypass).
- [ ] UI adopts the Telegram theme colors (light/dark switch actually changes the UI).
- [ ] Prompt/provider panels persist via API (no `(stub)` toasts left).

## D2. Structured logging + aiogram error middleware

**Files:** [apps/bot/main.py](apps/bot/main.py), `apps/bot/tg/middlewares.py` (new), route handlers.

**Steps:**
1. Add `request_id` (FastAPI middleware) and include `bot_id`/`update_id`/`request_id` in log context on the webhook path.
2. Add aiogram error middleware: catch handler exceptions, log with context, reply a safe message.

**Acceptance:**
- [ ] Every webhook log line carries `bot_id`, `update_id`, `request_id`.
- [ ] A raised exception inside a handler is caught, logged, and the user gets a graceful reply (no 500 loop / no unhandled traceback killing the update).

## D3. Test suite + CI

**Files:** `tests/` (new), `.github/workflows/ci.yml` (new), remove/convert [test_persistence.py](test_persistence.py).

**Steps:**
1. Pytest (async) with FastAPI `TestClient`/`httpx.AsyncClient`.
2. Required tests: dynamic webhook routing (known/unknown token, secret check), **tenant isolation in retrieval (B2)**, ingestion happy-path status transitions, initData validation (A2).
3. Convert `test_persistence.py` into a real pytest or delete it.
4. GitHub Actions: `uv sync`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest`.

**Acceptance:**
- [ ] `uv run pytest` passes locally with the required tests present.
- [ ] Tenant isolation test fails if the `bot_id` filter is removed (prove it guards the invariant).
- [ ] CI workflow runs on push/PR and is green.

---

# Out of scope for now (deliberate)

- Full LangGraph runtime (WORKPLAN Phase 4) — only if bot behaviors truly diverge; B3 leaves the seam.
- External task queue (celery/arq) — `asyncio`/`BackgroundTasks` is enough at current scale.
- Guest mode (Bot API 10.0), Topics-in-private-chats threading — nice-to-have, revisit after core.
- Migrating the Mini App to a bundler (Vite) — only if the frontend grows.

# Definition of done (whole roadmap)

- Bot answers real questions from uploaded docs, streaming, with source citations, isolated per `bot_id`.
- Webhook + Mini App are authenticated; migrations manage the schema.
- Automated tests prove tenant isolation and webhook/auth behavior; CI is green.
