# DataMind Infrastructure

Docker Compose orchestration for the full DataMind stack.

## Services (8 total)

```
┌─────────────────────────────────────────────────┐
│                 nginx (:80)                      │
│  /api/* → backend:8000                          │
│  /ws    → backend:8000 (WebSocket upgrade)      │
│  /*     → frontend:3000                         │
└──────────────┬──────────────┬───────────────────┘
               │              │
      ┌────────▼──┐    ┌──────▼────┐
      │  backend  │    │ frontend  │
      │  :8000    │    │  :3000    │
      └─────┬─────┘    └───────────┘
            │
   ┌────────┼────────────┐
   │        │            │
┌──▼──┐  ┌──▼──┐  ┌─────▼──────┐
│ pg  │  │redis│  │celery_worker│
│:5432│  │:6379│  │(concurrency=2)│
└─────┘  └─────┘  └─────┬──────┘
                         │
                  ┌──────▼──────┐
                  │ celery_beat │
                  │(SINGLETON!) │
                  └─────────────┘
```

## Startup Order
1. **postgres** + **redis** start (no deps)
2. Health checks confirm they're ready (pg_isready, redis-cli ping)
3. **migrate** runs `alembic upgrade head`, then exits
4. **backend**, **celery_worker**, **celery_beat** start (depend on migrate success)
5. **frontend** starts
6. **nginx** starts last (depends on backend + frontend)

## Files
| File | Purpose |
|------|---------|
| `docker-compose.yml` | Production stack (8 services) |
| `docker-compose.dev.yml` | Development overrides (hot reload, debug) |
| `docker-compose.test.yml` | Test environment |
| `nginx.conf` | Reverse proxy routing (⚠️ no SSL, no security headers) |

## Critical Operational Notes
- **Celery Beat MUST be singleton** — 2 instances = every task fires twice
- **NEXT_PUBLIC_* vars are build args**, not runtime env — Next.js inlines at build time
- **Health check gap**: /api/v1/health returns static JSON, doesn't verify DB/Redis connectivity
- **No SSL/TLS** — all traffic is unencrypted HTTP (production blocker)

## Environment Variables (required in .env)
```
DB_PASSWORD=<strong-password>
JWT_SECRET=<random-256-bit>
JWT_REFRESH_SECRET=<random-256-bit>
ENCRYPTION_KEY=<random-key>
ANTHROPIC_API_KEY=<your-api-key>
REDIS_URL=redis://redis:6379/0
DATABASE_URL=postgresql+asyncpg://datamind:${DB_PASSWORD}@postgres:5432/datamind_app
```

## Commands
```bash
make dev              # Start full stack
make build            # Build all images
docker compose -f docker/docker-compose.yml logs -f backend  # Tail backend logs
```
