# DataMind — Claude Code Context

## Project Identity
DataMind is an AI-powered BI platform. Monorepo with 3 layers:
- **backend/** — Python 3.12, FastAPI, SQLAlchemy 2 (async), Celery, Anthropic Claude API
- **frontend/** — Next.js 14 (App Router), TypeScript, Tailwind, Zustand, SWR, Recharts
- **docker/** — Docker Compose (8 services: postgres, redis, backend, frontend, nginx, celery_worker, celery_beat, migrate)

## Critical Rules
1. **Always read files before modifying them** — never edit blind
2. **Commit after each logical unit of work** — don't batch massive changes
3. **Update STATUS.md before ending any session** — this is the handoff document
4. **Never let parallel agents modify the same file** — split by file ownership
5. **Reference fixes by ID** from improvement-analysis.txt (e.g., "Fix #3: Wire AIEngine")

## Key Documentation Files
| File | Purpose | When to read |
|------|---------|-------------|
| `STATUS.md` | What's done, what's next, blockers | **Every session start** |
| `improvement-analysis.txt` | 30 prioritized improvements with impact/effort | When planning work |
| `product-documentation.txt` | Full architecture deep-dive (700+ lines) | When you need to understand a subsystem |
| `prompting-strategy.txt` | How to structure sessions, prompt templates | When starting a new work batch |

## Project Structure (abbreviated)
```
backend/app/
  ai/           → SQL generation, prompts, analysis, conversation, anomaly detection
  api/v1/       → Route handlers (auth, chat, connections, dashboards, alerts, query, schema, export)
  connectors/   → DB adapters (postgres, mysql, sqlite, csv, excel)
  core/         → security.py, sql_validator.py, middleware.py, database.py, exceptions.py
  models/       → SQLAlchemy ORM (user, org, connection, dashboard, widget, alert, chat_session, etc.)
  schemas/      → Pydantic request/response models
  services/     → Business logic (ai_engine, auth, connection_manager, query_executor, etc.)
  tasks/        → Celery tasks (alert_checker, schema_refresh, report_generator)
  config.py     → Settings class (reads .env, rejects insecure defaults)
  main.py       → FastAPI app factory

frontend/src/
  app/          → Next.js pages: (auth)/login,register  (dashboard)/chat,connections,dashboards,alerts
  components/   → React components: chat/, dashboard/, charts/, alerts/, layout/, shared/, ui/
  hooks/        → SWR data hooks: use-connections, use-dashboards, use-chat, use-websocket
  stores/       → Zustand: chat-store, connection-store, ui-store
  lib/          → api-client.ts, utils.ts, constants.ts
  types/        → TypeScript interfaces including ListResponse<T>

docker/
  docker-compose.yml      → Production (8 services)
  docker-compose.dev.yml  → Development overrides
  nginx.conf              → Reverse proxy (no SSL yet)
```

## Architecture Patterns
- **ListResponse<T>** envelope on all list endpoints: `{ data: T[], count: number }`
- **Multi-tenancy** via org_id on every model + every query WHERE clause
- **JWT dual tokens**: access (60min, JWT_SECRET) + refresh (7d, JWT_REFRESH_SECRET)
- **SQL safety**: sqlglot AST parsing blocks INSERT/UPDATE/DELETE/DROP in AI-generated queries
- **Connector strategy pattern**: BaseConnector → PostgresConnector, MySQLConnector, SQLiteConnector, CSVConnector, ExcelConnector
- **ConnectionManager split**: get_connector(id, org_id, db) for API / get_connector_internal(id, db) for Celery

## Git History
```
c167cbd fix: comprehensive QA fixes (security, data flow, features, infra) — 56 files, 688 insertions
7c6fa81 feat: implement Phases 4-6 (dashboards, alerts, export, CI/CD)
a0363fc feat: implement complete DataMind platform (Phases 1-3)
5907105 Initial commit
```

## Known Critical Bugs (from improvement-analysis.txt)
1. **Fix #1**: auth_service.py refresh calls decode_jwt() instead of decode_refresh_jwt() — refresh tokens always fail
2. **Fix #2**: alert_checker.py calls get_connector() with wrong args (missing org_id) — all alerts crash
3. **Fix #3**: /chat/message REST endpoint returns placeholder string — AIEngine exists but isn't wired

## Current Priority Queue
See STATUS.md for what's next. The improvement-analysis.txt ranks 30 items by impact/effort.
Top 6 (1-2 weeks, 1 engineer): Fix #1-3 bugs, SSL/TLS, Redis rate limiting, security headers.
