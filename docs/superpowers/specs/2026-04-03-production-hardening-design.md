# MiroFish Production Hardening Design Spec

**Date:** 2026-04-03
**Scope:** P1 (Security), P2 (Quality), P3 (Polish) — 9 sub-projects
**Implementation order:** A → B → C → G → D → F → E → H → I

---

## Sub-project A: Security Hardening

### CORS Lockdown
- Replace wildcard `origins: "*"` in `app/__init__.py` with configurable `ALLOWED_ORIGINS` env var
- Format: comma-separated list (e.g., `https://mirofish.app,https://www.mirofish.app`)
- Default: `http://localhost:3000` (dev only)
- Applied via Flask-CORS `resources` parameter

### Rate Limiting
- Wire up already-installed `flask-limiter` with Redis backend (`REDIS_URL`)
- Limits:
  - Auth endpoints (`/api/auth/login`, `/api/auth/signup`): **5/minute** per IP
  - Token refresh: **10/minute** per IP
  - File uploads (`/api/graph/upload`): **10/hour** per user
  - LLM-heavy endpoints (ontology, graph build, simulation start): **20/hour** per user
  - Default all other endpoints: **100/minute** per IP
- Key function: authenticated user ID when available, else remote IP

### Security Headers
- Add `@app.after_request` middleware setting:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains` (production only)
  - `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'` (adjust if frontend loads external fonts/CDN)
  - `X-XSS-Protection: 0`
  - `Referrer-Policy: strict-origin-when-cross-origin`

### HTTPS Enforcement
- `@app.before_request` handler: redirect HTTP → HTTPS when `FLASK_DEBUG=False`
- Check `X-Forwarded-Proto` header (Railway terminates TLS at proxy)
- Skip for health check endpoint

### Debug Default Fix
- Change `FLASK_DEBUG` default from `'True'` to `'False'` in `config.py`
- Conditional traceback exposure: only include `traceback` key in error responses when `DEBUG=True`

### Files modified:
- `backend/app/__init__.py` — CORS config, security headers middleware, HTTPS redirect
- `backend/app/config.py` — ALLOWED_ORIGINS, FLASK_DEBUG default, REDIS_URL
- `backend/app/api/*.py` — Remove traceback exposure from error responses in production
- Rate limiter initialization in app factory or dedicated `extensions.py`

---

## Sub-project B: Docker Hardening

### Non-root User
- Add to Dockerfile:
  ```dockerfile
  RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
  USER appuser
  ```
- Place after all `COPY` and build steps, before `EXPOSE`/`CMD`
- `uploads/` volume mount ownership handled by `chown`

### Production Environment Defaults
- `ENV FLASK_DEBUG=False`
- `ENV PYTHONDONTWRITEBYTECODE=1`
- `ENV PYTHONUNBUFFERED=1`

### Files modified:
- `Dockerfile`

---

## Sub-project C: Monitoring & Error Tracking (Sentry)

### Backend Sentry
- Add `sentry-sdk[flask]` to `pyproject.toml`
- Initialize in `app/__init__.py`, gated on `SENTRY_DSN` env var
- Configuration:
  - `traces_sample_rate`: 0.1 (10% of transactions)
  - `profiles_sample_rate`: 0.1
  - Slow transaction threshold: 5s
  - Attach user context (`user.id`, `user.email`) from JWT via `before_send`
- Integrations: FlaskIntegration, SqlalchemyIntegration

### Frontend Sentry
- Add `@sentry/vue` to `frontend/package.json`
- Initialize in `main.js`, gated on `VITE_SENTRY_DSN` env var
- Integrations: BrowserTracing, Vue Router instrumentation
- Capture: JS errors, unhandled promise rejections, page load performance

### Structured Logging Cleanup
- Remove `request.get_json()` debug logging in `app/__init__.py` (PII leak: passwords)
- Add request ID middleware: generate UUID per request, attach to `g.request_id`, include in all log output via custom formatter
- Sanitize sensitive fields (`password`, `token`, `api_key`, `secret`) from any remaining debug logs

### New env vars:
- `SENTRY_DSN` (backend)
- `VITE_SENTRY_DSN` (frontend)

### Files modified:
- `backend/pyproject.toml` — add sentry-sdk
- `backend/app/__init__.py` — Sentry init, request ID middleware, remove PII logging
- `backend/app/utils/logger.py` — request ID in log formatter, field sanitization
- `frontend/package.json` — add @sentry/vue
- `frontend/src/main.js` — Sentry init

---

## Sub-project D: API Documentation (Flasgger)

### Setup
- Add `flasgger` to `pyproject.toml`
- Initialize in app factory with OpenAPI 3.0 config
- Swagger UI served at `/api/docs` (public, no auth)

### Documentation approach
- Add YAML docstrings to each route function in `backend/app/api/*.py`
- Document: request parameters, request body schema, response schema, auth requirements, error codes
- Group by blueprint (Auth, Graph, Simulation, Report, Predict, Billing)

### Files modified:
- `backend/pyproject.toml` — add flasgger
- `backend/app/__init__.py` — Flasgger init
- `backend/app/api/auth.py` — route docstrings
- `backend/app/api/graph.py` — route docstrings
- `backend/app/api/simulation.py` — route docstrings
- `backend/app/api/report.py` — route docstrings
- `backend/app/api/predict.py` — route docstrings
- `backend/app/api/billing.py` — route docstrings

---

## Sub-project E: Test Coverage (Full Stack)

### Backend Tests

**Framework:** pytest + pytest-flask + pytest-asyncio
**Database:** Separate test PostgreSQL (`TEST_DATABASE_URL`), transaction rollback per test

**Test files to create:**
- `tests/test_auth.py` — extend existing (signup, login, refresh, logout, me, profile update)
- `tests/test_graph_api.py` — project CRUD, file upload, ontology extraction, graph build + status polling
- `tests/test_simulation_api.py` — create, prepare, start, stop, run status, profiles, actions, timeline, interview
- `tests/test_report_api.py` — create, sections, status, download, chat
- `tests/test_predict_api.py` — start prediction, status polling, cancel
- `tests/test_billing_api.py` — checkout, portal, webhook signature verification, plan limits, usage
- `tests/test_middleware.py` — require_auth, require_active_plan, service_auth, error handlers
- `tests/test_repositories.py` — extend existing (all 7 repos, CRUD for all 13 models)
- `tests/test_services/` — unit tests for graph_builder, simulation_runner, report_agent, ontology_generator (LLM calls mocked)

**Mocking strategy:** All external services mocked:
- LLM/OpenAI calls → mock responses
- Neo4j/Graphiti → mock client
- Resend email → mock
- Dodo payments → mock
- Sentry → disabled in tests
- Redis → use fakeredis

### Frontend Tests

**Framework:** Vitest + Vue Test Utils + @testing-library/vue

**Test files to create:**
- `tests/components/Step1GraphBuild.spec.js` — file upload, graph build trigger, status display
- `tests/components/Step2EnvSetup.spec.js` — entity display, configuration
- `tests/components/Step3Simulation.spec.js` — simulation config, profile generation
- `tests/components/Step4Report.spec.js` — report generation, section display
- `tests/components/Step5Interaction.spec.js` — chat interface, message rendering
- `tests/components/GraphPanel.spec.js` — D3 visualization rendering
- `tests/views/Login.spec.js` — form validation, submit, error states
- `tests/views/Signup.spec.js` — form validation, submit, error states
- `tests/views/Dashboard.spec.js` — project list, create, delete
- `tests/views/WorkspaceView.spec.js` — tab navigation, data loading
- `tests/views/PredictionProgress.spec.js` — progress polling, completion
- `tests/store/auth.spec.js` — all actions, token management, computed properties
- `tests/api/interceptors.spec.js` — 401 refresh, 403 redirect, retry logic, timeout handling
- `tests/router/guards.spec.js` — auth redirect, plan gating, public route bypass

### CI Integration
- Add test job to `.github/workflows/docker-image.yml` (or new `ci.yml`)
- Run on push to any branch + PR to main
- Steps: install deps → run backend tests → run frontend tests → report coverage
- Block merge if tests fail

### Files modified:
- `backend/pyproject.toml` — add test deps (pytest-flask, fakeredis, pytest-cov)
- `backend/tests/conftest.py` — update fixtures for full test DB + mocking
- `backend/tests/` — all new test files listed above
- `frontend/package.json` — add vitest, @vue/test-utils, @testing-library/vue
- `frontend/vitest.config.js` — test configuration
- `frontend/src/tests/` — all new test files listed above
- `.github/workflows/ci.yml` — new CI workflow for tests

---

## Sub-project F: Caching Layer (Redis)

### Infrastructure
- Add `redis` to `pyproject.toml`
- Add Redis service to `docker-compose.yml`
- Configure via `REDIS_URL` env var (Railway provides this natively)

### Cache Service
- New file: `backend/app/services/cache_service.py`
- Methods: `get(key)`, `set(key, value, ttl)`, `invalidate(key)`, `invalidate_pattern(pattern)`
- Decorator: `@cached(key_template, ttl)` for service methods
- Serialization: JSON for simple values, pickle for complex objects

### What gets cached:
| Data | Key pattern | TTL | Invalidation trigger |
|------|-------------|-----|---------------------|
| Graph entities | `entities:{graph_id}` | 10 min | Graph rebuild |
| Simulation profiles | `profiles:{simulation_id}` | 30 min | Profile regeneration |
| Simulation config | `sim_config:{simulation_id}` | 30 min | Config update |
| Project list | `projects:{user_id}` | 5 min | Project create/update/delete |

### What is NOT cached:
- LLM responses (too variable, context-dependent)
- Report chat (real-time interaction)
- Billing data (must always be fresh)
- Auth tokens (already short-lived)

### Shared Redis instance:
- Same `REDIS_URL` used by flask-limiter (sub-project A) and cache service
- Different key prefixes: `ratelimit:` vs `cache:`

### Files modified:
- `backend/pyproject.toml` — add redis
- `backend/app/config.py` — REDIS_URL
- `backend/app/services/cache_service.py` — new
- `backend/app/services/zep_entity_reader.py` — add caching
- `backend/app/repositories/simulation_repo.py` — add caching
- `backend/app/repositories/project_repo.py` — add caching
- `docker-compose.yml` — add Redis service

---

## Sub-project G: Graceful Shutdown

### Signal Handling
- Register `SIGTERM` and `SIGINT` handlers in `run.py`
- On signal: call `simulation_runner.shutdown_all()`

### Shutdown Process
- `simulation_runner.py` adds `shutdown_all()` method:
  1. Send `SIGTERM` to all tracked child processes
  2. Wait up to 30 seconds for graceful exit
  3. Send `SIGKILL` to any remaining
  4. Mark interrupted simulations as `status='interrupted'` in database

### Crash Recovery
- On app startup in `app/__init__.py`: scan for simulations with `status='running'`
- Mark any found as `status='interrupted'` (stale from previous crash)
- Log warning for each recovered simulation

### UI Impact
- Frontend already handles various simulation statuses
- `interrupted` status shown with appropriate message ("Simulation was interrupted — restart to continue")

### Files modified:
- `backend/run.py` — signal handlers
- `backend/app/services/simulation_runner.py` — `shutdown_all()` method
- `backend/app/__init__.py` — crash recovery on startup
- `backend/app/models/db_models.py` — ensure `interrupted` is a valid status value

---

## Sub-project H: Feature Flags

### Configuration
- New file: `backend/feature_flags.json`
  ```json
  {
    "enable_reddit_simulation": true,
    "enable_billing": true,
    "enable_report_chat": true,
    "max_simulation_rounds_override": null
  }
  ```

### Module
- New file: `backend/app/utils/feature_flags.py`
- `is_enabled(flag_name: str) -> bool` — checks env var `FF_<FLAG_NAME>` first, falls back to JSON
- `get_value(flag_name: str) -> Any` — same precedence, returns typed value
- JSON loaded once at startup (module-level)
- Env var values: `"true"`/`"false"` for bools, strings/numbers parsed automatically

### Usage
- Service layer checks flags before gated features
- Example: `if not is_enabled('enable_reddit_simulation'): return error`
- No frontend flags — backend gates sufficient for v1

### Files modified:
- `backend/feature_flags.json` — new
- `backend/app/utils/feature_flags.py` — new
- `backend/app/services/simulation_runner.py` — check reddit flag
- `backend/app/api/report.py` — check report_chat flag
- `backend/app/api/billing.py` — check billing flag

---

## Sub-project I: Legal Pages

### New Vue Components
- `frontend/src/views/TermsOfService.vue` — standard SaaS terms template
- `frontend/src/views/PrivacyPolicy.vue` — standard privacy policy template

### Content Sections

**Terms of Service:**
- Acceptance of terms
- Account registration and security
- Acceptable use policy
- Intellectual property (user content vs platform)
- AI-generated content disclaimer
- Service availability and SLA
- Limitation of liability
- Termination
- Governing law
- Changes to terms

**Privacy Policy:**
- Data collected (account info, uploaded documents, simulation data, usage analytics)
- How data is used
- Third-party services (OpenAI/LLM provider, Neo4j, Dodo Payments, Sentry, Resend)
- Data retention and deletion
- User rights (access, correction, deletion)
- Cookies and tracking
- Children's privacy
- Contact information

### Routing
- `/terms` — public, no auth required
- `/privacy` — public, no auth required

### Integration
- Footer links in `App.vue`
- Links in signup flow ("By signing up, you agree to our Terms and Privacy Policy")

### Clearly marked as templates requiring legal review before launch.

### Files modified:
- `frontend/src/views/TermsOfService.vue` — new
- `frontend/src/views/PrivacyPolicy.vue` — new
- `frontend/src/router/index.js` — add routes
- `frontend/src/App.vue` — footer links
- `frontend/src/views/Signup.vue` — legal consent links

---

## New Environment Variables Summary

| Variable | Sub-project | Required | Default |
|----------|-------------|----------|---------|
| `ALLOWED_ORIGINS` | A | No | `http://localhost:3000` |
| `REDIS_URL` | A, F | Yes (prod) | `redis://localhost:6379` |
| `SENTRY_DSN` | C | No | None (disabled) |
| `VITE_SENTRY_DSN` | C | No | None (disabled) |
| `TEST_DATABASE_URL` | E | No (test only) | — |
| `FF_*` | H | No | Falls back to JSON |

---

## New Dependencies Summary

**Backend (`pyproject.toml`):**
- `sentry-sdk[flask]` — error tracking
- `flasgger` — API docs
- `redis` — caching + rate limiter backend
- `fakeredis` — test dependency
- `pytest-flask` — test dependency
- `pytest-cov` — test coverage

**Frontend (`package.json`):**
- `@sentry/vue` — error tracking
- `vitest` — test framework
- `@vue/test-utils` — Vue component testing
- `@testing-library/vue` — DOM testing utilities
