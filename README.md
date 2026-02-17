# DataMind - AI-Powered Business Intelligence

DataMind is an open-source business intelligence platform that lets non-technical
users ask questions about their data in plain English. An AI engine translates
natural language into safe, validated SQL, executes it against connected databases,
and returns interactive charts, summaries, and anomaly alerts -- all within a
multi-tenant, organisation-scoped workspace.

---

## Features

- **Natural-Language Queries** -- ask questions like "What were our top 10 products
  last quarter?" and get results instantly.
- **AI-Generated SQL** -- Claude translates questions into read-only SQL,
  validated at the AST level with sqlglot before execution.
- **Interactive Dashboards** -- drag-and-drop dashboard builder with
  AI-recommended chart types.
- **Multi-Source Connectors** -- connect PostgreSQL, MySQL, SQL Server, BigQuery,
  Snowflake, or CSV/Excel uploads.
- **Anomaly Detection** -- automated statistical anomaly detection on scheduled
  queries with configurable alerts.
- **Multi-Tenancy** -- organisation-scoped data isolation with role-based access
  control (owner, admin, member, viewer).
- **Real-Time Updates** -- WebSocket-powered live query progress and dashboard
  refresh.
- **Credential Encryption** -- data-source passwords encrypted at rest with
  Fernet (AES-256).
- **Rate Limiting** -- per-IP sliding-window throttle to protect the API.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2 (async), Alembic |
| AI | Anthropic Claude API, sqlglot |
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, Zustand |
| Database | PostgreSQL 16 |
| Cache / Queue | Redis 7, Celery |
| Infra | Docker, Docker Compose, Nginx, GitHub Actions CI |

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2+
- An [Anthropic API key](https://console.anthropic.com/)

### 1. Clone the repository

```bash
git clone https://github.com/your-org/datamind.git
cd datamind
```

### 2. Create an environment file

```bash
cp .env.example .env
# Edit .env and fill in the required values (see Environment Variables below)
```

### 3. Start with Docker Compose

```bash
docker compose -f docker/docker-compose.yml up --build
```

The application will be available at:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/v1 |
| API docs (Swagger) | http://localhost:8000/docs |

### 4. Run database migrations

```bash
make migrate
# or
cd backend && alembic upgrade head
```

### 5. (Optional) Seed demo data

```bash
make seed
```

---

## Architecture

```
                    +------------+
                    |   Nginx    |  :80
                    +-----+------+
                         / \
                        /   \
               +-------+     +--------+
               |Frontend|     |Backend |
               |Next.js |     |FastAPI |
               | :3000  |     | :8000  |
               +--------+     +---+----+
                                  |
                    +-------------+-------------+
                    |             |             |
              +-----+---+  +----+----+  +-----+-----+
              |PostgreSQL|  |  Redis  |  | Celery    |
              |  :5432   |  |  :6379  |  | Worker(s) |
              +----------+  +---------+  +-----------+
```

**Request flow for a natural-language query:**

1. User types a question in the frontend.
2. Frontend sends the question via WebSocket to the backend.
3. The AI engine (Claude) generates a SQL query.
4. `SQLSafetyValidator` parses the SQL into an AST and rejects anything
   that is not a pure read-only `SELECT`.
5. The validated query is executed against the user's connected data source
   (scoped by `org_id`).
6. Results are streamed back via WebSocket with AI-generated chart
   recommendations and a plain-English summary.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://datamind:yourpassword@localhost:5432/datamind_app` | Async PostgreSQL connection string |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Redis connection string |
| `ANTHROPIC_API_KEY` | Yes | -- | Anthropic API key for Claude |
| `JWT_SECRET` | Yes | `change-me` | Secret for signing JWT tokens |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | Access token lifetime in minutes |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token lifetime in days |
| `ENCRYPTION_KEY` | Yes | `change-me` | Key for encrypting data-source credentials |
| `CORS_ORIGINS` | No | `["http://localhost:3000"]` | Allowed CORS origins (JSON list) |
| `DEBUG` | No | `false` | Enable debug mode |
| `DB_PASSWORD` | Yes | -- | PostgreSQL password (used by Docker Compose) |
| `NEXTAUTH_SECRET` | Yes | -- | NextAuth.js session secret |
| `NEXTAUTH_URL` | No | -- | NextAuth.js callback URL |

---

## Development Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Start the dev server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Database migrations

```bash
# Create a new migration
make migration msg="add_new_table"

# Apply all migrations
make migrate
```

---

## Testing

```bash
# Run all tests (unit + integration)
make test

# Unit tests only (with coverage)
make test-unit

# Integration tests (requires Docker services)
make test-integration

# End-to-end tests (Playwright)
make test-e2e

# Linting (backend + frontend)
make lint
```

---

## Project Structure

```
.
+-- backend/
|   +-- app/
|   |   +-- ai/             # AI engine: SQL generation, analysis, anomaly detection
|   |   +-- api/             # FastAPI routes and WebSocket handlers
|   |   +-- connectors/      # Database connector adapters
|   |   +-- core/            # Middleware, security, SQL validator, database setup
|   |   +-- models/          # SQLAlchemy ORM models
|   |   +-- schemas/         # Pydantic request/response schemas
|   |   +-- services/        # Business logic layer
|   |   +-- tasks/           # Celery async tasks
|   |   +-- config.py        # Application settings
|   |   +-- main.py          # FastAPI app factory
|   +-- tests/               # Unit, integration, AI tests
|   +-- alembic/             # Database migrations
|   +-- Dockerfile
|   +-- requirements.txt
+-- frontend/
|   +-- app/                 # Next.js App Router pages
|   +-- components/          # React components
|   +-- hooks/               # Custom React hooks
|   +-- lib/                 # API client, utilities
|   +-- stores/              # Zustand state stores
|   +-- types/               # TypeScript type definitions
|   +-- Dockerfile
+-- docker/
|   +-- docker-compose.yml
|   +-- docker-compose.dev.yml
|   +-- docker-compose.test.yml
|   +-- nginx.conf
+-- docs/
|   +-- SECURITY.md
+-- Makefile
```

---

## Contributing

1. Fork the repository and create your branch from `main`.
2. Write tests for any new functionality.
3. Ensure `make lint` and `make test` pass before submitting.
4. Open a pull request with a clear description of the changes.

Please read [docs/SECURITY.md](docs/SECURITY.md) for details on the security
model and responsible disclosure policy.

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for
details.
