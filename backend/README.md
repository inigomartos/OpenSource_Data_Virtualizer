# DataMind Backend

FastAPI async backend powering the DataMind BI platform.

## Tech Stack
- Python 3.12, FastAPI, Uvicorn (ASGI)
- SQLAlchemy 2 (async) + asyncpg/aiomysql/aiosqlite
- Celery + Redis (task queue)
- Anthropic Claude API (AI engine)
- Alembic (migrations — currently empty, needs generation)

## Directory Structure
```
app/
├── ai/                 # AI layer
│   ├── prompts.py          # System prompts for Claude (CRITICAL — quality of all AI output depends on these)
│   ├── sql_generator.py    # NL → SQL via Claude, 3-level response parsing fallback
│   ├── analyze_and_visualize.py  # Query results → insight + chart config via Claude
│   ├── conversation.py     # Context compression (15K → 500 tokens per request)
│   ├── anomaly_detector.py # Z-score anomaly detection (placeholder)
│   └── schema_enricher.py  # Claude-powered column/table descriptions
│
├── api/v1/             # Route handlers
│   ├── auth.py             # Login, register, refresh (dual JWT)
│   ├── chat.py             # Chat sessions + messages (⚠️ REST endpoint is placeholder)
│   ├── connections.py      # DB connection CRUD (role-gated: admin/analyst)
│   ├── dashboards.py       # Dashboard + Widget CRUD, pin-from-chat, refresh
│   ├── alerts.py           # Alert CRUD, events, mark-read
│   ├── query.py            # Direct SQL execution, saved queries
│   ├── schema.py           # Schema introspection per connection
│   ├── export.py           # PDF (reportlab) + Excel (openpyxl) export
│   ├── upload.py           # CSV/Excel file upload
│   └── audit.py            # Audit log viewer (admin only)
│
├── connectors/         # Database adapters (strategy pattern)
│   ├── base.py             # BaseConnector ABC: 6 abstract methods
│   ├── postgres.py         # asyncpg, SSL, _quote_ident, connection pool
│   ├── mysql.py            # aiomysql, backtick escaping, cursor-based
│   ├── sqlite.py           # aiosqlite, file-based, PRAGMA introspection
│   ├── csv_connector.py    # Pandas → SQLite transformation
│   └── excel_connector.py  # Multi-sheet → SQLite (one table per sheet)
│
├── core/               # Framework layer
│   ├── security.py         # JWT create/decode (dual keys), Fernet encrypt/decrypt, bcrypt
│   ├── sql_validator.py    # sqlglot AST-based validation (blocks INSERT/UPDATE/DELETE/DROP)
│   ├── database.py         # Async engine + session (pool_size=20, max_overflow=10)
│   ├── middleware.py        # Rate limiter (in-memory ⚠️), request logging, CORS
│   └── exceptions.py       # DataMindException hierarchy → HTTP status mapping
│
├── models/             # SQLAlchemy ORM (all have org_id for multi-tenancy)
├── schemas/            # Pydantic v2 (model_validate, from_attributes, ListResponse<T>)
├── services/           # Business logic
│   ├── ai_engine.py        # Full 7-step pipeline: schema→compress→generate→validate→execute→analyze→respond
│   ├── auth_service.py     # Register/login/refresh (⚠️ refresh calls wrong decode function)
│   ├── connection_manager.py  # get_connector(org-scoped) vs get_connector_internal(Celery)
│   └── query_executor.py   # Execute with pool cleanup (try/finally close)
│
├── tasks/              # Celery background tasks
│   ├── celery_app.py       # Config, beat schedule (alerts: 60s, schemas: 6h)
│   ├── alert_checker.py    # Check all active alerts (⚠️ broken: wrong get_connector args)
│   ├── schema_refresh.py   # Introspect all connections, diff & update metadata
│   └── report_generator.py # Placeholder
│
├── config.py           # Settings(BaseSettings) — rejects insecure defaults at startup
└── main.py             # App factory, exception handlers, middleware registration
```

## Key Patterns
- **ListResponse[T]** envelope on all list endpoints: `{"data": [...], "count": N}`
- **org_id scoping** on every query for multi-tenancy isolation
- **Dependency injection**: `get_db` (async session), `get_current_user` (JWT → User), `require_role`
- **SQL validation**: sqlglot AST walk, not regex — catches subquery injection

## Running
```bash
# With Docker
make dev

# Standalone
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Tests
```bash
pytest tests/ -v
```
⚠️ Coverage is ~10%. Tests exist only for sql_validator and auth endpoints.
