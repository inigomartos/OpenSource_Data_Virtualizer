# DataMind Security Model

This document describes the defense-in-depth security architecture used throughout
DataMind. Every layer is designed so that a failure in one does not compromise the
entire system.

---

## 1. Defense-in-Depth Overview

DataMind employs **seven security layers**, each independently enforced:

| Layer | Mechanism | Where |
|-------|-----------|-------|
| 1. Network | Nginx reverse proxy, TLS termination | `docker/nginx.conf` |
| 2. Rate Limiting | Per-IP sliding-window throttle | `backend/app/core/middleware.py` |
| 3. Authentication | JWT access + refresh tokens (HS256) | `backend/app/core/security.py` |
| 4. Authorization | Role-based access (owner / admin / member / viewer) | `backend/app/dependencies.py` |
| 5. Multi-Tenancy | Organisation-scoped queries (`org_id` filter on every DB call) | `backend/app/services/` |
| 6. SQL Safety | AST-level validation via sqlglot (read-only SELECT only) | `backend/app/core/sql_validator.py` |
| 7. Credential Encryption | AES-256 via Fernet (data-source passwords at rest) | `backend/app/core/security.py` |

---

## 2. SQL Safety Validation

All AI-generated SQL is validated **before execution** using the `SQLSafetyValidator`
class, which relies on [sqlglot](https://github.com/tobymao/sqlglot) to parse the
query into an Abstract Syntax Tree (AST).

### Rules enforced

- Only a **single** SQL statement is accepted per request.
- The statement **must** be a `SELECT`.
- The AST is walked recursively; any node matching a blocked expression type is
  rejected:
  - `INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, `ALTER`
  - `Command` (e.g. `COPY`, `VACUUM`)
  - `Transaction` (`BEGIN`, `COMMIT`, `ROLLBACK`)
  - `SET` (session variable mutations)

### Why AST, not regex?

Regular expressions can be bypassed with encoding tricks, comments, or creative
whitespace. Parsing the SQL into a typed tree and walking every node eliminates
entire classes of injection attacks because the validator operates on the
**semantic structure**, not the raw text.

---

## 3. Authentication (JWT)

- **Access tokens** expire after a configurable period (default 60 minutes).
- **Refresh tokens** expire after 7 days and can only be used to obtain a new
  access token.
- Tokens are signed with `HS256` using a server-side secret (`JWT_SECRET`).
- Passwords are hashed with **bcrypt** (via `passlib`).
- Token payloads include `sub` (user ID), `org_id`, `role`, `exp`, and `type`
  (`access` or `refresh`).

### Recommendations for production

- Rotate `JWT_SECRET` periodically using a secret manager.
- Store refresh tokens in HTTP-only, Secure, SameSite cookies.
- Implement token revocation via a Redis deny-list for logout and password changes.

---

## 4. Multi-Tenancy Isolation

Every database query that touches tenant data is scoped by `org_id`:

```python
query = select(DataSource).where(DataSource.org_id == current_user.org_id)
```

This ensures that:

- Users can **never** read or modify data belonging to another organisation.
- Even if an attacker obtains a valid JWT for one organisation, they cannot
  access another organisation's resources.
- Database-level row security policies can be layered on top for additional
  hardening.

---

## 5. Credential Encryption (AES-256)

Data-source connection credentials (passwords, connection strings) are encrypted
at rest using **Fernet** symmetric encryption, which internally uses AES-128-CBC
with HMAC-SHA256 for authenticated encryption.

- The encryption key is derived from the `ENCRYPTION_KEY` environment variable
  via SHA-256, then base64-encoded into a valid Fernet key.
- Credentials are encrypted before being stored in the database and decrypted
  only at the moment a connection is established.
- The `ENCRYPTION_KEY` must be kept secret and should be managed through a
  secret manager (e.g. AWS Secrets Manager, HashiCorp Vault) in production.

### Key rotation

To rotate the encryption key:

1. Decrypt all stored credentials with the old key.
2. Re-encrypt with the new key.
3. Update the `ENCRYPTION_KEY` environment variable.
4. Restart all backend instances.

---

## 6. Rate Limiting

The `RateLimitMiddleware` enforces a **per-IP sliding-window** rate limit:

- Default: **100 requests per minute** per client IP.
- Health-check endpoints (`/health`) are excluded.
- When the limit is exceeded, the server responds with HTTP `429 Too Many Requests`
  and a `Retry-After` header.

The built-in implementation uses in-memory storage and is suitable for
single-instance deployments. For horizontally scaled production deployments,
replace the in-memory store with a Redis-backed counter (e.g. using
`redis.incr` with TTL).

---

## 7. Additional Hardening

### CORS

- Allowed origins are explicitly configured via `CORS_ORIGINS` (default:
  `http://localhost:3000`).
- Credentials, all methods, and all headers are permitted only for the
  configured origins.

### Docker

- Backend and frontend containers run as **non-root** users.
- Multi-stage builds keep production images minimal (no build tools, no
  development dependencies).

### CI/CD

- Every pull request runs linting (`ruff`, `mypy`, `eslint`), unit tests
  with coverage, and Docker image builds.
- Secrets used in CI are scoped to the test environment and are not
  production values.

---

## Responsible Disclosure

If you discover a security vulnerability in DataMind, we ask that you
**report it responsibly**:

1. **Do not** open a public GitHub issue.
2. Email **security@datamind.dev** with:
   - A description of the vulnerability.
   - Steps to reproduce.
   - The potential impact.
3. We will acknowledge receipt within **48 hours** and aim to release a fix
   within **14 days** for critical issues.
4. We will credit you in the release notes (unless you prefer to remain
   anonymous).

Thank you for helping keep DataMind and its users safe.
