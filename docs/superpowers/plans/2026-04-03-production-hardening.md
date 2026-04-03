# Production Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden MiroFish for public release across security, quality, and operational polish (P1/P2/P3).

**Architecture:** 9 independent sub-projects executed sequentially. Each produces a working, testable commit. Shared infrastructure (Redis, Sentry) is introduced early so later tasks can build on it.

**Tech Stack:** Flask, Vue 3, Redis, Sentry, Flasgger, Vitest, pytest, GitHub Actions

---

## Task 1: Security Hardening — CORS, Rate Limiting, Headers, HTTPS, Debug Fix

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/__init__.py`
- Modify: `backend/app/middleware/errors.py`
- Modify: `backend/app/api/graph.py`
- Modify: `backend/app/api/simulation.py`
- Modify: `backend/app/api/report.py`
- Modify: `backend/pyproject.toml`

### Step 1.1: Add config values

- [ ] Add `ALLOWED_ORIGINS` and `REDIS_URL` to `backend/app/config.py`:

```python
# In class Config, after BETTAFISH_SERVICE_KEY line (~line 94):

# CORS
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000')

# Redis (used for rate limiting and caching)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
```

- [ ] Change the DEBUG default from `'True'` to `'False'` on line 25:

```python
DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
```

### Step 1.2: Fix CORS configuration

- [ ] In `backend/app/__init__.py` line 43, replace the wildcard CORS:

```python
# Old:
CORS(app, resources={r"/api/*": {"origins": "*"}})

# New:
origins = [o.strip() for o in Config.ALLOWED_ORIGINS.split(',') if o.strip()]
CORS(app, resources={r"/api/*": {"origins": origins, "supports_credentials": True}})
```

### Step 1.3: Add rate limiting

- [ ] Add `redis` to `backend/pyproject.toml` dependencies list (after `flask-limiter>=3.5`):

```toml
"redis>=5.0",
```

- [ ] In `backend/app/__init__.py`, after the CORS setup (~line 43), initialize the limiter:

```python
# Rate limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def _rate_limit_key():
    """Use authenticated user ID if available, else remote IP."""
    from flask import g
    user = getattr(g, 'current_user', None)
    if user and hasattr(user, 'id'):
        return f"user:{user.id}"
    return get_remote_address()

limiter = Limiter(
    app=app,
    key_func=_rate_limit_key,
    storage_uri=Config.REDIS_URL,
    default_limits=["100 per minute"],
    strategy="fixed-window",
)
app.limiter = limiter  # Store on app for blueprint access
```

- [ ] Add rate limits to auth endpoints. In `backend/app/api/auth.py`, after the blueprint imports at the top, add:

```python
from flask import current_app

def _get_limiter():
    return current_app.limiter
```

Then decorate the login and signup routes:

```python
@auth_bp.route('/login', methods=['POST'])
def login():
    _get_limiter().limit("5 per minute")(lambda: None)()
    # ... existing code
```

**Simpler approach:** Use `@limiter.limit()` directly. Since the limiter is on the app, access it via the blueprint's `before_request`:

In `backend/app/__init__.py`, after creating the limiter, add specific endpoint limits:

```python
# Auth rate limits
limiter.limit("5 per minute", key_func=get_remote_address)(
    app.view_functions.get('auth.login') or (lambda: None)
)
```

**Better approach — use limiter decorators after blueprint registration:**

After all `app.register_blueprint(...)` calls in `__init__.py` (~line 128), add:

```python
# Apply rate limits to specific endpoints
auth_limits = {
    'auth.login': '5 per minute',
    'auth.signup': '5 per minute',
    'auth.refresh': '10 per minute',
}
for endpoint, limit_str in auth_limits.items():
    view_fn = app.view_functions.get(endpoint)
    if view_fn:
        app.view_functions[endpoint] = limiter.limit(limit_str, key_func=get_remote_address)(view_fn)

upload_limits = {
    'graph.upload_file': '10 per hour',
}
for endpoint, limit_str in upload_limits.items():
    view_fn = app.view_functions.get(endpoint)
    if view_fn:
        app.view_functions[endpoint] = limiter.limit(limit_str)(view_fn)

llm_limits = {
    'graph.generate_ontology': '20 per hour',
    'graph.build_graph': '20 per hour',
    'simulation.start_simulation': '20 per hour',
}
for endpoint, limit_str in llm_limits.items():
    view_fn = app.view_functions.get(endpoint)
    if view_fn:
        app.view_functions[endpoint] = limiter.limit(limit_str)(view_fn)
```

### Step 1.4: Add security headers middleware

- [ ] In `backend/app/__init__.py`, replace the existing `log_response` after_request handler (line 59-63) with one that also sets security headers:

```python
@app.after_request
def add_security_headers(response):
    logger = get_logger('mirofish.request')
    logger.debug(f"Response: {response.status_code}")

    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['X-XSS-Protection'] = '0'

    if not app.debug:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "connect-src 'self'"
        )

    return response
```

### Step 1.5: Add HTTPS enforcement

- [ ] In `backend/app/__init__.py`, modify the existing `log_request` before_request handler (line 52-57):

```python
@app.before_request
def before_request_handler():
    logger = get_logger('mirofish.request')

    # HTTPS enforcement (skip for health check and in debug mode)
    if not app.debug and request.path != '/health':
        forwarded_proto = request.headers.get('X-Forwarded-Proto', 'https')
        if forwarded_proto == 'http':
            from flask import redirect
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)

    # Request logging
    logger.debug(f"Request: {request.method} {request.path}")
```

- [ ] **Remove the PII-leaking line** (line 56-57 in the old code). Do NOT log `request.get_json()` — it contains passwords on login.

### Step 1.6: Strip traceback from production error responses

- [ ] In `backend/app/middleware/errors.py`, update the generic error handler to conditionally include traceback:

```python
def register_error_handlers(app):
    """Register centralized error handlers on the Flask app."""

    @app.errorhandler(AuthError)
    def handle_auth_error(e):
        return jsonify({"error": str(e), "code": "AUTH_ERROR"}), 401

    @app.errorhandler(ForbiddenError)
    def handle_forbidden(e):
        return jsonify({"error": str(e), "code": "FORBIDDEN"}), 403

    @app.errorhandler(NotFoundError)
    def handle_not_found(e):
        return jsonify({"error": str(e), "code": "NOT_FOUND"}), 404

    @app.errorhandler(ValidationError)
    def handle_validation(e):
        return jsonify({"error": str(e), "code": "VALIDATION_ERROR"}), 422

    @app.errorhandler(Exception)
    def handle_generic(e):
        logger.error(f"Unhandled exception: {traceback.format_exc()}")
        payload = {"error": "Internal server error", "code": "INTERNAL_ERROR"}
        if app.debug:
            payload["traceback"] = traceback.format_exc()
        return jsonify(payload), 500
```

- [ ] In all API blueprint files (`graph.py`, `simulation.py`, `report.py`), remove the `"traceback": traceback.format_exc()` lines from error response dicts. Replace every occurrence of:

```python
return jsonify({
    "success": False,
    "error": str(e),
    "traceback": traceback.format_exc()
}), 500
```

With:

```python
logger.error(f"Error: {traceback.format_exc()}")
return jsonify({
    "success": False,
    "error": str(e)
}), 500
```

**Files with traceback exposure to fix:**
- `backend/app/api/graph.py`: lines 333, 608, 683, 706
- `backend/app/api/simulation.py`: lines 87, 115, 147, 268, 679, 855, 897, 1074, 1148, 1259, 1380, 1417, 1447, 1500, 1575, 1780, 1850, 1911
- `backend/app/api/report.py`: lines 271, 405, 445, 486, 588, 622, 735, 779, 831, 876, 928, 990, 1025, 1074, 1109, 1160, 1201

### Step 1.7: Commit

- [ ] ```bash
git add backend/app/config.py backend/app/__init__.py backend/app/middleware/errors.py backend/app/api/graph.py backend/app/api/simulation.py backend/app/api/report.py backend/pyproject.toml
git commit -m "feat: security hardening — CORS, rate limiting, headers, HTTPS, debug fix"
```

---

## Task 2: Docker Hardening

**Files:**
- Modify: `Dockerfile`
- Modify: `docker-compose.yml`

### Step 2.1: Add non-root user and production defaults to Dockerfile

- [ ] Edit `Dockerfile`. After the `RUN cd frontend && npm run build` line and before `ENV FLASK_DEBUG=false`, add:

```dockerfile
# Production environment defaults
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
```

The existing `ENV FLASK_DEBUG=false` line stays as-is (already correct).

### Step 2.2: Add Redis to docker-compose.yml

- [ ] Replace `docker-compose.yml` contents:

```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: mirofish-redis
    restart: unless-stopped
    volumes:
      - redis-data:/data

  mirofish:
    image: ghcr.io/666ghj/mirofish:latest
    container_name: mirofish
    env_file:
      - .env
    environment:
      - REDIS_URL=redis://redis:6379/0
    ports:
      - "3000:3000"
      - "5001:5001"
    restart: unless-stopped
    volumes:
      - ./backend/uploads:/app/backend/uploads
    depends_on:
      - redis

volumes:
  redis-data:
```

### Step 2.3: Commit

- [ ] ```bash
git add Dockerfile docker-compose.yml
git commit -m "feat: Docker hardening — non-root user, Redis, production defaults"
```

---

## Task 3: Sentry Integration (Backend + Frontend)

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/__init__.py`
- Modify: `backend/app/utils/logger.py`
- Modify: `frontend/package.json`
- Modify: `frontend/src/main.js`
- Modify: `backend/app/config.py`

### Step 3.1: Add backend Sentry dependency

- [ ] Add to `backend/pyproject.toml` dependencies:

```toml
"sentry-sdk[flask]>=2.0",
```

- [ ] Add config in `backend/app/config.py` after the REDIS_URL line:

```python
# Sentry
SENTRY_DSN = os.environ.get('SENTRY_DSN', '')
```

- [ ] Run: `cd backend && uv sync`

### Step 3.2: Initialize Sentry in backend

- [ ] In `backend/app/__init__.py`, add Sentry initialization right after `app.config.from_object(config_class)` (before logging setup, ~line 23):

```python
# Initialize Sentry (must be before other imports)
if Config.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    sentry_sdk.init(
        dsn=Config.SENTRY_DSN,
        integrations=[FlaskIntegration(), SqlalchemyIntegration()],
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        send_default_pii=False,
    )
```

### Step 3.3: Add request ID middleware

- [ ] In `backend/app/__init__.py`, inside the `before_request_handler` function (from Task 1), add request ID generation at the top:

```python
import uuid

@app.before_request
def before_request_handler():
    from flask import g
    g.request_id = str(uuid.uuid4())[:8]
    # ... rest of the handler from Task 1
```

- [ ] Update `backend/app/utils/logger.py` to include request ID in log format. Change the `detailed_formatter` (line 56-58):

```python
detailed_formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] [rid:%(request_id)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

And add a filter class above `setup_logger`:

```python
class RequestIdFilter(logging.Filter):
    """Inject request_id into log records."""
    def filter(self, record):
        try:
            from flask import g, has_request_context
            if has_request_context():
                record.request_id = getattr(g, 'request_id', '-')
            else:
                record.request_id = '-'
        except Exception:
            record.request_id = '-'
        return True
```

Then add the filter to both handlers in `setup_logger`, after creating each handler:

```python
# After creating file_handler and console_handler:
request_id_filter = RequestIdFilter()
file_handler.addFilter(request_id_filter)
console_handler.addFilter(request_id_filter)
```

### Step 3.4: Add Sentry to frontend

- [ ] Run: `cd frontend && npm install @sentry/vue`

- [ ] Update `frontend/src/main.js`:

```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

const app = createApp(App)

// Sentry initialization (only if DSN is configured)
const sentryDsn = import.meta.env.VITE_SENTRY_DSN
if (sentryDsn) {
  import('@sentry/vue').then(Sentry => {
    Sentry.init({
      app,
      dsn: sentryDsn,
      integrations: [
        Sentry.browserTracingIntegration({ router }),
      ],
      tracesSampleRate: 0.1,
      replaysSessionSampleRate: 0,
      replaysOnErrorSampleRate: 0,
    })
  })
}

app.use(createPinia())
app.use(router)

app.mount('#app')
```

### Step 3.5: Commit

- [ ] ```bash
git add backend/pyproject.toml backend/app/__init__.py backend/app/utils/logger.py backend/app/config.py frontend/package.json frontend/package-lock.json frontend/src/main.js
git commit -m "feat: add Sentry error tracking (backend + frontend) with request ID logging"
```

---

## Task 4: Graceful Shutdown & Crash Recovery

**Files:**
- Modify: `backend/app/services/simulation_runner.py`
- Modify: `backend/app/__init__.py`
- Modify: `backend/app/models/db_models.py`

### Step 4.1: Add `interrupted` status to simulation model

- [ ] Check `backend/app/models/db_models.py` for the SimulationModel. If it uses a string `status` field (not an enum), no change is needed — `'interrupted'` can be stored directly. If it uses a Python Enum, add `INTERRUPTED = 'interrupted'` to that enum.

### Step 4.2: Enhance `cleanup_all_simulations` to mark DB records

- [ ] In `backend/app/services/simulation_runner.py`, find the `cleanup_all_simulations` classmethod (~line 1199). After the existing process termination logic and before clearing `cls._processes`, add:

```python
# Mark running simulations as interrupted in database
try:
    from ..db import get_db
    from ..repositories.simulation_repo import SimulationRepository
    with get_db() as session:
        for sim_id in list(cls._run_states.keys()):
            state = cls._run_states[sim_id]
            if state.runner_status in [RunnerStatus.RUNNING, RunnerStatus.STARTING]:
                state.runner_status = RunnerStatus.STOPPED
                state.completed_at = datetime.now().isoformat()
                state.error = "Server shutdown — simulation interrupted"
                cls._save_run_state(state)
                try:
                    sim = SimulationRepository(session).get_by_id(sim_id)
                    if sim and sim.status == 'running':
                        sim.status = 'interrupted'
                        session.commit()
                        logger.info(f"Marked simulation {sim_id} as interrupted")
                except Exception as db_err:
                    logger.warning(f"Failed to update DB for {sim_id}: {db_err}")
except Exception as e:
    logger.warning(f"Failed to mark simulations as interrupted: {e}")
```

### Step 4.3: Add crash recovery on startup

- [ ] In `backend/app/__init__.py`, after the existing "Recover stale tasks" block (~line 103-112), add:

```python
# Recover simulations stuck in 'running' state from previous crash
try:
    from .db import get_db
    with get_db() as session:
        from .repositories.simulation_repo import SimulationRepository
        sim_repo = SimulationRepository(session)
        stuck = sim_repo.find_by_status('running')
        for sim in stuck:
            sim.status = 'interrupted'
            if should_log_startup:
                logger.warning(f"Recovered stuck simulation: {sim.id} (was 'running', now 'interrupted')")
        if stuck:
            session.commit()
            if should_log_startup:
                logger.info(f"Recovered {len(stuck)} stuck simulations from previous crash")
except Exception as e:
    logger.warning(f"Simulation recovery skipped: {e}")
```

- [ ] Ensure `SimulationRepository` has a `find_by_status` method. If not, add it:

```python
def find_by_status(self, status: str):
    """Find all simulations with a given status."""
    return self.session.query(SimulationModel).filter_by(status=status).all()
```

### Step 4.4: Commit

- [ ] ```bash
git add backend/app/services/simulation_runner.py backend/app/__init__.py backend/app/models/db_models.py backend/app/repositories/simulation_repo.py
git commit -m "feat: graceful shutdown with simulation interrupt and crash recovery"
```

---

## Task 5: API Documentation (Flasgger)

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/__init__.py`
- Modify: `backend/app/api/auth.py`
- Modify: `backend/app/api/graph.py`
- Modify: `backend/app/api/simulation.py`
- Modify: `backend/app/api/report.py`
- Modify: `backend/app/api/predict.py`
- Modify: `backend/app/api/billing.py`

### Step 5.1: Install flasgger

- [ ] Add to `backend/pyproject.toml` dependencies:

```toml
"flasgger>=0.9.7",
```

- [ ] Run: `cd backend && uv sync`

### Step 5.2: Initialize Flasgger in app factory

- [ ] In `backend/app/__init__.py`, after registering error handlers (~line 116), add:

```python
# API documentation
from flasgger import Swagger
swagger_config = {
    "headers": [],
    "specs": [{
        "endpoint": "apispec",
        "route": "/api/docs/apispec.json",
    }],
    "static_url_path": "/api/docs/static",
    "swagger_ui": True,
    "specs_route": "/api/docs/",
}
swagger_template = {
    "info": {
        "title": "MiroFish API",
        "description": "AI-Powered Swarm Intelligence Engine API",
        "version": "1.0.0",
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Bearer token. Format: 'Bearer {token}'"
        }
    },
    "security": [{"Bearer": []}],
}
Swagger(app, config=swagger_config, template=swagger_template)
```

### Step 5.3: Add docstrings to auth endpoints

- [ ] Add YAML docstrings to each route in `backend/app/api/auth.py`. Example for login:

```python
@auth_bp.route('/login', methods=['POST'])
def login():
    """User login
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: user@example.com
            password:
              type: string
              example: mypassword123
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            success:
              type: boolean
            access_token:
              type: string
            refresh_token:
              type: string
      401:
        description: Invalid credentials
    """
```

Add similar docstrings for: `signup`, `refresh`, `logout`, `get_me`, `update_me`.

### Step 5.4: Add docstrings to remaining blueprints

- [ ] Add YAML docstrings to key endpoints in `graph.py`, `simulation.py`, `report.py`, `predict.py`, `billing.py`. At minimum document: HTTP method, tags, parameters, request body schema, response schema, auth requirement, and error codes.

Focus on the most-used endpoints first:
- `graph.py`: `create_project`, `upload_file`, `generate_ontology`, `build_graph`, `task_status`
- `simulation.py`: `create_simulation`, `start_simulation`, `get_run_status`, `get_simulation_actions`
- `report.py`: `create_report`, `get_report`, `chat_with_report`
- `predict.py`: `start_prediction`, `get_prediction_status`
- `billing.py`: `create_checkout`, `get_limits`, `get_usage`

### Step 5.5: Verify Swagger UI loads

- [ ] Run: `cd backend && uv run python run.py`
- [ ] Open: `http://localhost:5001/api/docs/`
- [ ] Verify the Swagger UI renders and shows all documented endpoints

### Step 5.6: Commit

- [ ] ```bash
git add backend/pyproject.toml backend/app/__init__.py backend/app/api/
git commit -m "feat: add OpenAPI documentation via Flasgger at /api/docs"
```

---

## Task 6: Redis Caching Layer

**Files:**
- Create: `backend/app/services/cache_service.py`
- Modify: `backend/app/__init__.py`
- Modify: `backend/app/repositories/project_repo.py`
- Modify: `backend/app/services/zep_entity_reader.py`

### Step 6.1: Create cache service

- [ ] Create `backend/app/services/cache_service.py`:

```python
"""Redis caching service with decorator support."""

import json
import functools
import hashlib
from typing import Optional, Any

import redis

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.cache')

_redis_client: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    """Get or create Redis connection. Returns None if unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        _redis_client = redis.from_url(
            Config.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
        )
        _redis_client.ping()
        logger.info("Redis connected")
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}")
        _redis_client = None
        return None


def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    r = get_redis()
    if not r:
        return None
    try:
        raw = r.get(f"cache:{key}")
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.debug(f"Cache get error for {key}: {e}")
        return None


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Set value in cache with TTL in seconds."""
    r = get_redis()
    if not r:
        return
    try:
        r.setex(f"cache:{key}", ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.debug(f"Cache set error for {key}: {e}")


def cache_invalidate(key: str) -> None:
    """Delete a specific cache key."""
    r = get_redis()
    if not r:
        return
    try:
        r.delete(f"cache:{key}")
    except Exception:
        pass


def cache_invalidate_pattern(pattern: str) -> None:
    """Delete all cache keys matching a pattern."""
    r = get_redis()
    if not r:
        return
    try:
        keys = r.keys(f"cache:{pattern}")
        if keys:
            r.delete(*keys)
    except Exception:
        pass


def cached(key_template: str, ttl: int = 300):
    """
    Decorator for caching function results.

    Usage:
        @cached("entities:{graph_id}", ttl=600)
        def get_entities(graph_id):
            ...

    Key template uses function argument names for formatting.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key from function args
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            try:
                cache_key = key_template.format(**bound.arguments)
            except KeyError:
                # If key template can't be resolved, skip cache
                return func(*args, **kwargs)

            # Check cache
            result = cache_get(cache_key)
            if result is not None:
                return result

            # Call function and cache result
            result = func(*args, **kwargs)
            if result is not None:
                cache_set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
```

### Step 6.2: Add caching to entity reader

- [ ] In `backend/app/services/zep_entity_reader.py`, import and use the cache for `filter_defined_entities`:

```python
from .cache_service import cache_get, cache_set, cache_invalidate

class ZepEntityReader:
    def filter_defined_entities(self, graph_id, defined_entity_types=None, enrich_with_edges=True):
        # Check cache (only for unfiltered requests)
        if not defined_entity_types:
            cache_key = f"entities:{graph_id}"
            cached = cache_get(cache_key)
            if cached is not None:
                from ..models.entity_result import EntityResult  # or whatever the return type is
                return cached  # adjust if return type needs reconstruction

        # ... existing code ...
        result = ...  # existing logic

        # Cache the result
        if not defined_entity_types and result:
            cache_set(f"entities:{graph_id}", result.to_dict(), ttl=600)

        return result
```

### Step 6.3: Add caching to project list

- [ ] In `backend/app/repositories/project_repo.py`, add cache invalidation on project mutations:

```python
from ..services.cache_service import cache_invalidate_pattern

# In create/update/delete methods, after the DB operation:
cache_invalidate_pattern(f"projects:{user_id}*")
```

### Step 6.4: Commit

- [ ] ```bash
git add backend/app/services/cache_service.py backend/app/services/zep_entity_reader.py backend/app/repositories/project_repo.py
git commit -m "feat: add Redis caching layer for entities and project lists"
```

---

## Task 7: Backend Test Coverage

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/tests/conftest.py`
- Create: `backend/tests/test_graph_api.py`
- Create: `backend/tests/test_simulation_api.py`
- Create: `backend/tests/test_report_api.py`
- Create: `backend/tests/test_predict_api.py`
- Create: `backend/tests/test_billing_api.py`
- Create: `backend/tests/test_middleware.py`
- Create: `backend/tests/test_cache_service.py`

### Step 7.1: Add test dependencies

- [ ] Update `backend/pyproject.toml` dev dependencies:

```toml
[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-flask>=1.3.0",
    "pytest-cov>=5.0.0",
    "fakeredis>=2.21.0",
]
```

- [ ] Run: `cd backend && uv sync --group dev`

### Step 7.2: Update conftest for broader patching

- [ ] In `backend/tests/conftest.py`, extend the `app` fixture to also patch additional imports used by blueprints:

```python
@pytest.fixture
def app(test_engine):
    """Create a Flask test app with SQLite-backed DB sessions."""
    TestSession = sessionmaker(bind=test_engine)

    @contextmanager
    def _test_get_db():
        session = TestSession()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # Patch get_db across all modules that import it
    patches = [
        patch("app.db.get_db", _test_get_db),
        patch("app.api.auth.get_db", _test_get_db),
        patch("app.api.graph.get_db", _test_get_db),
        patch("app.api.simulation.get_db", _test_get_db),
        patch("app.api.report.get_db", _test_get_db),
        patch("app.api.predict.get_db", _test_get_db),
        patch("app.api.billing.get_db", _test_get_db),
        patch("app.middleware.auth.get_db", _test_get_db),
    ]

    for p in patches:
        p.start()

    from app import create_app
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    flask_app._test_get_db = _test_get_db
    yield flask_app

    for p in patches:
        p.stop()
```

Add a helper fixture for creating authenticated requests:

```python
@pytest.fixture
def auth_headers(client):
    """Create a test user and return auth headers."""
    # Sign up a test user
    client.post('/api/auth/signup', json={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    # Login
    resp = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    data = resp.get_json()
    token = data.get('access_token', '')
    return {'Authorization': f'Bearer {token}'}
```

### Step 7.3: Write middleware tests

- [ ] Create `backend/tests/test_middleware.py`:

```python
"""Tests for auth middleware and error handlers."""

def test_unauthenticated_request_returns_401(client):
    """Protected endpoint without token returns 401."""
    resp = client.get('/api/graph/list')
    assert resp.status_code == 401

def test_invalid_token_returns_401(client):
    """Invalid JWT returns 401."""
    resp = client.get('/api/graph/list', headers={'Authorization': 'Bearer invalid.token.here'})
    assert resp.status_code == 401

def test_authenticated_request_succeeds(client, auth_headers):
    """Valid token allows access to protected endpoints."""
    resp = client.get('/api/graph/list', headers=auth_headers)
    assert resp.status_code == 200

def test_health_check(client):
    """Health endpoint returns ok."""
    resp = client.get('/health')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'ok'

def test_security_headers_present(client):
    """Security headers are set on responses."""
    resp = client.get('/health')
    assert resp.headers.get('X-Content-Type-Options') == 'nosniff'
    assert resp.headers.get('X-Frame-Options') == 'DENY'
```

### Step 7.4: Write cache service tests

- [ ] Create `backend/tests/test_cache_service.py`:

```python
"""Tests for Redis cache service."""

import pytest
from unittest.mock import patch

def test_cache_get_set():
    """Cache set then get returns the value."""
    import fakeredis
    fake_redis = fakeredis.FakeRedis(decode_responses=True)

    with patch('app.services.cache_service.get_redis', return_value=fake_redis):
        from app.services.cache_service import cache_get, cache_set
        cache_set("test_key", {"foo": "bar"}, ttl=60)
        result = cache_get("test_key")
        assert result == {"foo": "bar"}

def test_cache_miss_returns_none():
    """Cache get for missing key returns None."""
    import fakeredis
    fake_redis = fakeredis.FakeRedis(decode_responses=True)

    with patch('app.services.cache_service.get_redis', return_value=fake_redis):
        from app.services.cache_service import cache_get
        result = cache_get("nonexistent")
        assert result is None

def test_cache_invalidate():
    """Cache invalidate removes the key."""
    import fakeredis
    fake_redis = fakeredis.FakeRedis(decode_responses=True)

    with patch('app.services.cache_service.get_redis', return_value=fake_redis):
        from app.services.cache_service import cache_get, cache_set, cache_invalidate
        cache_set("to_delete", "value", ttl=60)
        cache_invalidate("to_delete")
        assert cache_get("to_delete") is None

def test_cache_unavailable_returns_none():
    """When Redis is unavailable, cache operations return None gracefully."""
    with patch('app.services.cache_service.get_redis', return_value=None):
        from app.services.cache_service import cache_get, cache_set
        cache_set("key", "val")  # should not raise
        assert cache_get("key") is None
```

### Step 7.5: Write billing webhook test

- [ ] Create `backend/tests/test_billing_api.py`:

```python
"""Tests for billing API endpoints."""

def test_get_limits_requires_auth(client):
    """Limits endpoint requires authentication."""
    resp = client.get('/api/billing/limits')
    assert resp.status_code == 401

def test_get_limits_returns_plan_info(client, auth_headers):
    """Authenticated user gets plan limits."""
    resp = client.get('/api/billing/limits', headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'success' in data

def test_get_usage_requires_auth(client):
    """Usage endpoint requires authentication."""
    resp = client.get('/api/billing/usage')
    assert resp.status_code == 401
```

### Step 7.6: Write graph API tests

- [ ] Create `backend/tests/test_graph_api.py`:

```python
"""Tests for graph API endpoints."""

def test_list_projects_empty(client, auth_headers):
    """New user has no projects."""
    resp = client.get('/api/graph/list', headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True

def test_create_project(client, auth_headers):
    """Create a new project."""
    resp = client.post('/api/graph/project', headers=auth_headers, json={
        'name': 'Test Project',
        'description': 'A test project',
        'seed_question': 'What will happen?'
    })
    assert resp.status_code in [200, 201]
    data = resp.get_json()
    assert data['success'] is True

def test_create_project_requires_auth(client):
    """Project creation requires authentication."""
    resp = client.post('/api/graph/project', json={'name': 'Test'})
    assert resp.status_code == 401

def test_upload_rejects_invalid_extension(client, auth_headers):
    """Upload rejects files with disallowed extensions."""
    from io import BytesIO
    data = {'file': (BytesIO(b'content'), 'malware.exe')}
    resp = client.post('/api/graph/upload', headers=auth_headers, data=data, content_type='multipart/form-data')
    # Should return an error (either 400 or 422)
    assert resp.status_code in [400, 422] or (resp.status_code == 200 and not resp.get_json().get('success'))
```

### Step 7.7: Run tests and verify

- [ ] ```bash
cd backend && uv run pytest tests/ -v --tb=short
```

Expected: All new tests pass. Existing tests still pass.

### Step 7.8: Commit

- [ ] ```bash
git add backend/pyproject.toml backend/tests/
git commit -m "feat: add backend test coverage for middleware, cache, billing, and graph APIs"
```

---

## Task 8: Frontend Test Setup + Tests

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/vitest.config.js`
- Create: `frontend/src/__tests__/store/auth.spec.js`
- Create: `frontend/src/__tests__/api/interceptors.spec.js`
- Create: `frontend/src/__tests__/router/guards.spec.js`

### Step 8.1: Install test dependencies

- [ ] Run:
```bash
cd frontend && npm install -D vitest @vue/test-utils @testing-library/vue jsdom
```

- [ ] Add test script to `frontend/package.json`:

```json
"scripts": {
  "dev": "vite --host",
  "build": "vite build",
  "preview": "vite preview",
  "test": "vitest run",
  "test:watch": "vitest"
}
```

### Step 8.2: Create vitest config

- [ ] Create `frontend/vitest.config.js`:

```javascript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['src/__tests__/**/*.spec.js'],
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
})
```

### Step 8.3: Write auth store tests

- [ ] Create `frontend/src/__tests__/store/auth.spec.js`:

```javascript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../../store/auth'

// Mock localStorage
const localStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn(key => store[key] || null),
    setItem: vi.fn((key, value) => { store[key] = value }),
    removeItem: vi.fn(key => { delete store[key] }),
    clear: vi.fn(() => { store = {} }),
  }
})()
Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock })

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorageMock.clear()
  })

  it('starts unauthenticated', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
  })

  it('setTokens stores tokens in localStorage', () => {
    const store = useAuthStore()
    store.setTokens('access123', 'refresh456')
    expect(localStorage.setItem).toHaveBeenCalledWith('access_token', 'access123')
    expect(localStorage.setItem).toHaveBeenCalledWith('refresh_token', 'refresh456')
  })

  it('clearTokens removes tokens', () => {
    const store = useAuthStore()
    store.clearTokens()
    expect(localStorage.removeItem).toHaveBeenCalledWith('access_token')
    expect(localStorage.removeItem).toHaveBeenCalledWith('refresh_token')
    expect(store.isAuthenticated).toBe(false)
  })
})
```

### Step 8.4: Write API interceptor tests

- [ ] Create `frontend/src/__tests__/api/interceptors.spec.js`:

```javascript
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock axios before importing the module
vi.mock('axios', () => {
  const interceptors = {
    request: { use: vi.fn() },
    response: { use: vi.fn() },
  }
  return {
    default: {
      create: vi.fn(() => ({
        interceptors,
        defaults: { headers: { common: {} } },
      })),
    },
  }
})

describe('API Service', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  it('exports a requestWithRetry function', async () => {
    const { requestWithRetry } = await import('../../api/index.js')
    expect(typeof requestWithRetry).toBe('function')
  })

  it('requestWithRetry retries on failure', async () => {
    const { requestWithRetry } = await import('../../api/index.js')
    let callCount = 0
    const fn = () => {
      callCount++
      if (callCount < 3) throw new Error('fail')
      return 'success'
    }
    const result = await requestWithRetry(fn, 3, 1)
    expect(result).toBe('success')
    expect(callCount).toBe(3)
  })

  it('requestWithRetry throws after max retries', async () => {
    const { requestWithRetry } = await import('../../api/index.js')
    const fn = () => { throw new Error('always fails') }
    await expect(requestWithRetry(fn, 2, 1)).rejects.toThrow('always fails')
  })
})
```

### Step 8.5: Write router guard tests

- [ ] Create `frontend/src/__tests__/router/guards.spec.js`:

```javascript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createRouter, createWebHistory } from 'vue-router'
import { setActivePinia, createPinia } from 'pinia'

// Minimal mock of auth store
vi.mock('../../store/auth', () => ({
  useAuthStore: vi.fn(() => ({
    isAuthenticated: false,
    user: null,
    canCreateProjects: false,
    fetchUser: vi.fn(),
  })),
}))

describe('Router Guards', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('public routes are accessible without auth', async () => {
    const { default: router } = await import('../../router/index.js')

    // Navigate to home (public)
    await router.push('/')
    expect(router.currentRoute.value.path).toBe('/')
  })
})
```

### Step 8.6: Run frontend tests

- [ ] ```bash
cd frontend && npm test
```

Expected: All tests pass.

### Step 8.7: Commit

- [ ] ```bash
git add frontend/vitest.config.js frontend/package.json frontend/package-lock.json frontend/src/__tests__/
git commit -m "feat: add frontend test framework (Vitest) with store, API, and router tests"
```

---

## Task 9: CI/CD — Test Job in GitHub Actions

**Files:**
- Create: `.github/workflows/ci.yml`

### Step 9.1: Create CI workflow

- [ ] Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: mirofish_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: cd backend && uv sync --group dev

      - name: Run tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/mirofish_test
          LLM_API_KEY: test-key
          JWT_SECRET_KEY: test-secret
          FLASK_DEBUG: "False"
        run: cd backend && uv run pytest tests/ -v --tb=short

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Run tests
        run: cd frontend && npm test
```

### Step 9.2: Commit

- [ ] ```bash
git add .github/workflows/ci.yml
git commit -m "feat: add CI workflow for backend and frontend tests"
```

---

## Task 10: Feature Flags

**Files:**
- Create: `backend/feature_flags.json`
- Create: `backend/app/utils/feature_flags.py`

### Step 10.1: Create feature flags JSON

- [ ] Create `backend/feature_flags.json`:

```json
{
  "enable_reddit_simulation": true,
  "enable_billing": true,
  "enable_report_chat": true,
  "max_simulation_rounds_override": null
}
```

### Step 10.2: Create feature flags module

- [ ] Create `backend/app/utils/feature_flags.py`:

```python
"""Simple file + env var feature flag system."""

import os
import json
from ..utils.logger import get_logger

logger = get_logger('mirofish.feature_flags')

_flags = {}
_loaded = False


def _load_flags():
    """Load flags from JSON file (once)."""
    global _flags, _loaded
    if _loaded:
        return
    flags_path = os.path.join(os.path.dirname(__file__), '../../../feature_flags.json')
    try:
        with open(flags_path, 'r') as f:
            _flags = json.load(f)
        logger.info(f"Loaded {len(_flags)} feature flags")
    except FileNotFoundError:
        logger.warning("feature_flags.json not found, using empty defaults")
        _flags = {}
    _loaded = True


def is_enabled(flag_name: str) -> bool:
    """
    Check if a feature flag is enabled.
    Env var FF_<FLAG_NAME> takes precedence over JSON file.
    """
    # Check env var first
    env_key = f"FF_{flag_name.upper()}"
    env_val = os.environ.get(env_key)
    if env_val is not None:
        return env_val.lower() in ('true', '1', 'yes')

    # Fall back to JSON
    _load_flags()
    val = _flags.get(flag_name)
    if isinstance(val, bool):
        return val
    return bool(val)


def get_value(flag_name: str):
    """
    Get a feature flag value (any type).
    Env var FF_<FLAG_NAME> takes precedence.
    """
    env_key = f"FF_{flag_name.upper()}"
    env_val = os.environ.get(env_key)
    if env_val is not None:
        # Try to parse as JSON for typed values
        try:
            return json.loads(env_val)
        except (json.JSONDecodeError, ValueError):
            return env_val

    _load_flags()
    return _flags.get(flag_name)
```

### Step 10.3: Commit

- [ ] ```bash
git add backend/feature_flags.json backend/app/utils/feature_flags.py
git commit -m "feat: add simple config-based feature flag system"
```

---

## Task 11: Legal Pages (Terms of Service + Privacy Policy)

**Files:**
- Create: `frontend/src/views/TermsOfService.vue`
- Create: `frontend/src/views/PrivacyPolicy.vue`
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/views/Signup.vue`

### Step 11.1: Create Terms of Service page

- [ ] Create `frontend/src/views/TermsOfService.vue`:

```vue
<template>
  <div class="legal-page">
    <div class="legal-content">
      <h1>Terms of Service</h1>
      <p class="legal-notice">Last updated: [DATE] | This is a template — please have it reviewed by legal counsel before launch.</p>

      <h2>1. Acceptance of Terms</h2>
      <p>By accessing or using MiroFish ("the Service"), you agree to be bound by these Terms of Service. If you do not agree, do not use the Service.</p>

      <h2>2. Account Registration</h2>
      <p>You must provide accurate information when creating an account. You are responsible for maintaining the security of your account credentials and for all activity under your account.</p>

      <h2>3. Acceptable Use</h2>
      <p>You agree not to:</p>
      <ul>
        <li>Use the Service for any unlawful purpose</li>
        <li>Attempt to gain unauthorized access to any part of the Service</li>
        <li>Upload malicious files or content</li>
        <li>Interfere with the Service's operation or other users' access</li>
        <li>Use automated tools to scrape or extract data from the Service</li>
      </ul>

      <h2>4. Intellectual Property</h2>
      <p>You retain ownership of content you upload. By uploading content, you grant MiroFish a limited license to process it for the purpose of providing the Service. Simulation outputs and reports generated by the Service are provided for informational purposes.</p>

      <h2>5. AI-Generated Content Disclaimer</h2>
      <p>The Service uses artificial intelligence to generate predictions, simulations, and reports. These outputs are speculative and should not be relied upon as factual predictions. MiroFish makes no guarantees about the accuracy of AI-generated content.</p>

      <h2>6. Service Availability</h2>
      <p>We strive to maintain high availability but do not guarantee uninterrupted access. The Service may be temporarily unavailable for maintenance or updates.</p>

      <h2>7. Subscription and Billing</h2>
      <p>Paid plans are billed according to the pricing displayed at the time of purchase. You may cancel your subscription at any time. Refunds are handled according to our refund policy.</p>

      <h2>8. Limitation of Liability</h2>
      <p>To the maximum extent permitted by law, MiroFish shall not be liable for any indirect, incidental, special, or consequential damages arising from your use of the Service.</p>

      <h2>9. Termination</h2>
      <p>We may suspend or terminate your account if you violate these Terms. You may delete your account at any time by contacting support.</p>

      <h2>10. Changes to Terms</h2>
      <p>We may update these Terms from time to time. Continued use of the Service after changes constitutes acceptance of the new Terms.</p>

      <h2>11. Contact</h2>
      <p>For questions about these Terms, contact us at [CONTACT EMAIL].</p>

      <router-link to="/" class="back-link">Back to home</router-link>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.legal-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 60px 24px;
}

.legal-content h1 {
  font-size: 28px;
  margin-bottom: 8px;
}

.legal-notice {
  color: #666;
  font-size: 14px;
  margin-bottom: 32px;
  padding: 12px;
  background: #f5f5f5;
  border-left: 3px solid #000;
}

.legal-content h2 {
  font-size: 18px;
  margin-top: 28px;
  margin-bottom: 8px;
}

.legal-content p,
.legal-content ul {
  font-size: 15px;
  line-height: 1.7;
  color: #333;
}

.legal-content ul {
  padding-left: 24px;
}

.legal-content li {
  margin-bottom: 4px;
}

.back-link {
  display: inline-block;
  margin-top: 40px;
  color: #000;
  text-decoration: underline;
}
</style>
```

### Step 11.2: Create Privacy Policy page

- [ ] Create `frontend/src/views/PrivacyPolicy.vue`:

```vue
<template>
  <div class="legal-page">
    <div class="legal-content">
      <h1>Privacy Policy</h1>
      <p class="legal-notice">Last updated: [DATE] | This is a template — please have it reviewed by legal counsel before launch.</p>

      <h2>1. Information We Collect</h2>
      <p><strong>Account information:</strong> Name, email address, and password (hashed) when you create an account.</p>
      <p><strong>Uploaded content:</strong> Documents and files you upload for simulation processing.</p>
      <p><strong>Simulation data:</strong> Agent profiles, simulation configurations, and generated reports.</p>
      <p><strong>Usage data:</strong> Page views, feature usage, and error logs for improving the Service.</p>

      <h2>2. How We Use Your Information</h2>
      <ul>
        <li>To provide and improve the Service</li>
        <li>To process your simulations and generate reports</li>
        <li>To communicate with you about your account</li>
        <li>To detect and prevent abuse</li>
        <li>To analyze usage patterns and improve performance</li>
      </ul>

      <h2>3. Third-Party Services</h2>
      <p>We use the following third-party services to provide the Service:</p>
      <ul>
        <li><strong>LLM Provider (e.g., OpenAI):</strong> Processes text for ontology extraction, agent profiling, and report generation. Your uploaded content may be sent to the LLM provider for processing.</li>
        <li><strong>Neo4j:</strong> Stores knowledge graph data (entities and relationships).</li>
        <li><strong>Dodo Payments:</strong> Processes subscription payments. We do not store your payment card details.</li>
        <li><strong>Sentry:</strong> Collects error reports and performance data to help us fix bugs.</li>
        <li><strong>Resend:</strong> Sends transactional emails (account verification, notifications).</li>
      </ul>

      <h2>4. Data Retention</h2>
      <p>Your account data is retained as long as your account is active. Uploaded documents and simulation data are retained for the duration of your subscription. You may request deletion of your data at any time.</p>

      <h2>5. Your Rights</h2>
      <p>You have the right to:</p>
      <ul>
        <li>Access the personal data we hold about you</li>
        <li>Correct inaccurate data</li>
        <li>Request deletion of your data</li>
        <li>Export your data in a portable format</li>
      </ul>

      <h2>6. Cookies and Tracking</h2>
      <p>We use essential cookies for authentication (JWT tokens stored in localStorage). We use Sentry for error tracking. We do not use advertising cookies or trackers.</p>

      <h2>7. Children's Privacy</h2>
      <p>The Service is not intended for users under 16 years of age. We do not knowingly collect data from children.</p>

      <h2>8. Changes to This Policy</h2>
      <p>We may update this Privacy Policy from time to time. We will notify you of material changes via email or in-app notification.</p>

      <h2>9. Contact</h2>
      <p>For privacy-related questions or data requests, contact us at [CONTACT EMAIL].</p>

      <router-link to="/" class="back-link">Back to home</router-link>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.legal-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 60px 24px;
}

.legal-content h1 {
  font-size: 28px;
  margin-bottom: 8px;
}

.legal-notice {
  color: #666;
  font-size: 14px;
  margin-bottom: 32px;
  padding: 12px;
  background: #f5f5f5;
  border-left: 3px solid #000;
}

.legal-content h2 {
  font-size: 18px;
  margin-top: 28px;
  margin-bottom: 8px;
}

.legal-content p,
.legal-content ul {
  font-size: 15px;
  line-height: 1.7;
  color: #333;
}

.legal-content ul {
  padding-left: 24px;
}

.legal-content li {
  margin-bottom: 4px;
}

.back-link {
  display: inline-block;
  margin-top: 40px;
  color: #000;
  text-decoration: underline;
}
</style>
```

### Step 11.3: Add routes

- [ ] In `frontend/src/router/index.js`, add these routes in the `routes` array (after the Pricing route):

```javascript
{
  path: '/terms',
  name: 'Terms',
  component: () => import('../views/TermsOfService.vue'),
  meta: { public: true }
},
{
  path: '/privacy',
  name: 'Privacy',
  component: () => import('../views/PrivacyPolicy.vue'),
  meta: { public: true }
}
```

### Step 11.4: Add footer links to App.vue

- [ ] In `frontend/src/App.vue`, add a footer with legal links. Update the template:

```vue
<template>
  <div id="app-wrapper">
    <router-view />
    <footer class="app-footer" v-if="showFooter">
      <router-link to="/terms">Terms of Service</router-link>
      <span class="separator">|</span>
      <router-link to="/privacy">Privacy Policy</router-link>
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const showFooter = computed(() => {
  // Show footer on public pages and dashboard, hide during simulation workflow
  const footerRoutes = ['Home', 'Login', 'Signup', 'Dashboard', 'Pricing', 'Terms', 'Privacy']
  return footerRoutes.includes(route.name)
})
</script>
```

Add footer styles to the `<style>` section:

```css
.app-footer {
  text-align: center;
  padding: 20px;
  font-size: 13px;
  color: #666;
  border-top: 1px solid #eee;
}

.app-footer a {
  color: #666;
  text-decoration: none;
}

.app-footer a:hover {
  color: #000;
  text-decoration: underline;
}

.app-footer .separator {
  margin: 0 8px;
}
```

### Step 11.5: Add legal consent to Signup

- [ ] In `frontend/src/views/Signup.vue`, add a line before the submit button:

```html
<p class="legal-consent">
  By creating an account, you agree to our
  <router-link to="/terms">Terms of Service</router-link>
  and
  <router-link to="/privacy">Privacy Policy</router-link>.
</p>
```

Add styling:

```css
.legal-consent {
  font-size: 13px;
  color: #666;
  margin-bottom: 16px;
}

.legal-consent a {
  color: #000;
  text-decoration: underline;
}
```

### Step 11.6: Commit

- [ ] ```bash
git add frontend/src/views/TermsOfService.vue frontend/src/views/PrivacyPolicy.vue frontend/src/router/index.js frontend/src/App.vue frontend/src/views/Signup.vue
git commit -m "feat: add Terms of Service and Privacy Policy pages"
```

---

## Task 12: Update .env.example with new variables

**Files:**
- Modify: `.env.example`

### Step 12.1: Add new environment variables

- [ ] Add the following to `.env.example`:

```bash
# CORS (comma-separated origins, default: http://localhost:3000)
# ALLOWED_ORIGINS=https://yourdomain.com

# Redis (required for rate limiting and caching)
# REDIS_URL=redis://localhost:6379/0

# Sentry (optional — leave blank to disable)
# SENTRY_DSN=
# VITE_SENTRY_DSN=

# Feature flags (override JSON defaults via env vars)
# FF_ENABLE_REDDIT_SIMULATION=true
# FF_ENABLE_BILLING=true
# FF_ENABLE_REPORT_CHAT=true
```

### Step 12.2: Commit

- [ ] ```bash
git add .env.example
git commit -m "docs: add new environment variables to .env.example"
```
