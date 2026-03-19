# MiroFish Production Database, Multi-Tenancy & Auth Design

**Date:** 2026-03-19
**Status:** Approved
**Scope:** Sub-project #1 (Database & Multi-tenancy) + Sub-project #2 (Auth & User Management)

## 1. Overview

Migrate MiroFish from file-based storage to PostgreSQL, add JWT-based authentication with Google OAuth, and implement single-user data isolation. This is the foundation for all subsequent production features (billing, API keys, landing page).

### Goals
- Every piece of state (projects, simulations, reports, chat sessions) persisted in PostgreSQL
- Users can sign up, log in, and resume any project/report/chat from where they left off
- Data isolation: users see only their own data
- 14-day free trial built into the user model (billing integration comes in a later sub-project)
- Uploaded files stored on S3-compatible object storage (Cloudflare R2 or Railway volume)

### Non-Goals (deferred to later sub-projects)
- Team workspaces / collaboration
- Stripe billing integration
- Public API with API keys
- General rate limiting (login endpoint rate limiting IS in scope)

### Data Migration Strategy
- No migration of existing file-based data. Fresh start with PostgreSQL.
- Old file-based code removed in final cleanup step.

## 2. Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Database | PostgreSQL on Railway | Same platform as app, full control, no vendor lock-in |
| ORM | SQLAlchemy 2.0 + Alembic | Industry standard for Flask, typed models, migration support |
| Auth | JWT (access + refresh tokens) | Stateless, scales horizontally, no session store needed |
| Login methods | Email/password + Google OAuth | Covers most users; GitHub OAuth deferred |
| Password hashing | bcrypt via passlib (cost factor 12) | Industry standard, adaptive cost factor |
| Password requirements | Min 8 chars, no complexity rules | Simple but effective; haveibeenpwned check deferred |
| Migration strategy | Incremental with Repository pattern | Swap file → DB one model at a time, each step independently testable |
| Simulation logs | Separate `simulation_actions` table | Queryable per agent/round, scales to millions of rows |
| File uploads | S3-compatible object storage | Railway filesystem is ephemeral; files must persist across deploys |
| User deletion | Soft delete (30-day grace period) | Prevent accidental data loss; hard delete after 30 days |

## 3. Database Schema

### 3.1 users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),          -- NULL for OAuth-only users
    name VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    auth_provider VARCHAR(50) DEFAULT 'email',  -- 'email' | 'google'
    google_id VARCHAR(255) UNIQUE,
    plan VARCHAR(20) DEFAULT 'trial',    -- 'trial' | 'basic' | 'pro' | 'enterprise'
    trial_ends_at TIMESTAMP NOT NULL,    -- set to NOW() + 14 days on signup
    stripe_customer_id VARCHAR(255),
    deleted_at TIMESTAMP,                -- soft delete (NULL = active)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_id ON users(google_id);
```

### 3.2 refresh_tokens

```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,    -- SHA-256 hash of the token
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,                -- NULL = active
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);
```

### 3.3 projects

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    simulation_requirement TEXT,
    graph_id VARCHAR(255),               -- Zep Cloud graph ID
    status VARCHAR(50) DEFAULT 'created',
    -- Status values: created | ontology_generated | graph_building | graph_completed |
    --   env_setup | simulating | reporting | interacting | completed | failed
    current_step INT DEFAULT 1,          -- 1-5 workflow step (for resume)
    step_data JSONB DEFAULT '{}',        -- step-specific state for resume (see Section 6.1)
    ontology JSONB,                      -- extracted entity_types and edge_types
    analysis_summary TEXT,               -- LLM analysis of uploaded documents
    extracted_text TEXT,                  -- full extracted text from uploaded files
    chunk_size INT DEFAULT 500,
    chunk_overlap INT DEFAULT 50,
    seed_files JSONB DEFAULT '[]',       -- [{filename, size, storage_key, uploaded_at}]
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_projects_status ON projects(status);
```

### 3.4 tasks

Tracks long-running operations (graph builds, simulation prep, report generation). Replaces the current in-memory `TaskManager` singleton.

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,           -- 'ontology_generation' | 'graph_build' | 'simulation_prep' | 'simulation_run' | 'report_generation'
    status VARCHAR(50) DEFAULT 'pending', -- pending | running | completed | failed
    progress INT DEFAULT 0,              -- 0-100
    message TEXT,                        -- current status message
    result JSONB,                        -- task result data
    error TEXT,
    metadata JSONB DEFAULT '{}',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_tasks_status ON tasks(status);
```

### 3.5 simulations

```sql
CREATE TABLE simulations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    simulation_id VARCHAR(255),          -- legacy OASIS simulation ID
    enable_twitter BOOLEAN DEFAULT true,
    enable_reddit BOOLEAN DEFAULT true,
    config JSONB NOT NULL DEFAULT '{}',  -- full simulation config (rounds, actions, seed posts)
    config_reasoning TEXT,               -- LLM's reasoning for config choices
    entity_types JSONB DEFAULT '[]',     -- entity types used in this simulation
    status VARCHAR(50) DEFAULT 'pending', -- pending | running | completed | failed
    twitter_status VARCHAR(50),          -- per-platform status
    reddit_status VARCHAR(50),
    max_rounds INT DEFAULT 10,
    twitter_current_round INT DEFAULT 0,
    reddit_current_round INT DEFAULT 0,
    agent_count INT DEFAULT 0,
    process_pid INT,                     -- PID of running subprocess (NULL when not running)
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_simulations_project_id ON simulations(project_id);
```

### 3.6 agent_profiles

```sql
CREATE TABLE agent_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id UUID NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    agent_index INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255),
    bio TEXT,
    personality JSONB DEFAULT '{}',
    profile_data JSONB DEFAULT '{}',     -- full OASIS profile JSON
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_agent_profiles_simulation_id ON agent_profiles(simulation_id);
```

### 3.7 simulation_actions

```sql
CREATE TABLE simulation_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id UUID NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    round INT NOT NULL,
    agent_index INT NOT NULL,
    agent_name VARCHAR(255),
    platform VARCHAR(20),                -- 'twitter' | 'reddit'
    action_type VARCHAR(50),             -- CREATE_POST, LIKE_POST, REPOST, etc.
    content TEXT,                         -- post/comment text
    target_id VARCHAR(255),              -- ID of post being liked/reposted
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_sim_actions_simulation_id ON simulation_actions(simulation_id);
CREATE INDEX idx_sim_actions_round ON simulation_actions(simulation_id, round);
CREATE INDEX idx_sim_actions_agent ON simulation_actions(simulation_id, agent_index);
```

### 3.8 simulation_round_summaries

```sql
CREATE TABLE simulation_round_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id UUID NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    round INT NOT NULL,
    platform VARCHAR(20),
    summary JSONB NOT NULL,              -- {total_actions, action_breakdown, key_events}
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(simulation_id, round, platform)
);
CREATE INDEX idx_round_summaries_simulation ON simulation_round_summaries(simulation_id);
```

### 3.9 reports

```sql
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    simulation_id UUID REFERENCES simulations(id), -- direct link for lookup
    graph_id VARCHAR(255),               -- Zep graph ID used for this report
    simulation_requirement TEXT,          -- requirement text at time of generation
    title VARCHAR(500),
    summary TEXT,
    outline JSONB,                       -- {title, summary, sections: [{title, description}]}
    status VARCHAR(50) DEFAULT 'pending', -- pending | planning | generating | completed | failed
    markdown_content TEXT,               -- full assembled report
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
CREATE INDEX idx_reports_project_id ON reports(project_id);
CREATE INDEX idx_reports_simulation_id ON reports(simulation_id);
```

### 3.10 report_sections

```sql
CREATE TABLE report_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    section_index INT NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT,                         -- markdown content
    tool_calls JSONB DEFAULT '[]',       -- [{tool_name, parameters, result_summary}]
    status VARCHAR(50) DEFAULT 'pending', -- pending | generating | completed
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_report_sections_report_id ON report_sections(report_id);
```

### 3.11 report_logs

Agent reasoning logs and console logs per report. Served via API for the frontend log viewer.

```sql
CREATE TABLE report_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    log_type VARCHAR(20) NOT NULL,       -- 'agent' | 'console'
    entries JSONB NOT NULL DEFAULT '[]', -- array of log entries (agent_log.jsonl equivalent)
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_report_logs_report_id ON report_logs(report_id);
```

### 3.12 chat_sessions

```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    agent_type VARCHAR(50) NOT NULL,     -- 'report_agent' | 'sim_agent'
    agent_index INT,                     -- NULL for report_agent, agent index for sim_agent
    agent_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_chat_sessions_project_id ON chat_sessions(project_id);
```

### 3.13 chat_messages

```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,           -- 'user' | 'assistant'
    content TEXT NOT NULL,
    tool_calls JSONB,                    -- tool calls made during this message (if assistant)
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
```

**Total: 13 tables.**

## 4. Repository Pattern (Data Access Layer)

Each model gets a repository class that abstracts storage operations.

```
backend/app/repositories/
    __init__.py
    base.py              # BaseRepository with common CRUD + DB session management
    user_repo.py         # UserRepository
    project_repo.py      # ProjectRepository
    simulation_repo.py   # SimulationRepository (includes actions, profiles, round summaries)
    report_repo.py       # ReportRepository (includes sections, logs)
    chat_repo.py         # ChatRepository (sessions + messages)
    task_repo.py         # TaskRepository (replaces in-memory TaskManager)
```

### Interface example:

```python
class ProjectRepository:
    def create(self, user_id: str, name: str, requirement: str, ...) -> Project
    def get_by_id(self, project_id: str, user_id: str) -> Project | None
    def list_by_user(self, user_id: str, limit=20, offset=0) -> list[Project]
    def update(self, project_id: str, user_id: str, **kwargs) -> Project
    def delete(self, project_id: str, user_id: str) -> bool
```

Every repository method that reads/writes takes `user_id` — this enforces data isolation at the data access layer, not just at the API level.

### Database connection pooling:

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,      # detect stale connections
    pool_recycle=300,         # recycle connections every 5 min
)
```

## 5. Authentication System

### 5.1 JWT Token Flow

```
Signup/Login → Server returns {access_token (15min), refresh_token (7 days)}
    ↓
Frontend stores tokens in httpOnly cookies (not localStorage)
    ↓
Every API request includes Authorization: Bearer <access_token>
    ↓
When access_token expires → POST /api/auth/refresh with refresh_token
    ↓
Server returns new access_token + NEW refresh_token (rotation)
    ↓
Old refresh_token is immediately revoked
```

**Refresh token rotation:** Each refresh request issues a new refresh token and revokes the old one. If a stolen refresh token is used after the legitimate user has refreshed, the revocation check catches it and invalidates all tokens for that user (forced re-login).

### 5.2 Auth Endpoints

```
POST /api/auth/signup          # email + password + name → tokens
POST /api/auth/login           # email + password → tokens (rate limited: 5/min per IP)
POST /api/auth/refresh         # refresh_token → new access_token + new refresh_token
POST /api/auth/logout          # invalidate refresh_token
GET  /api/auth/me              # get current user profile
PUT  /api/auth/me              # update profile

GET  /api/auth/google           # redirect to Google OAuth
GET  /api/auth/google/callback  # Google OAuth callback → tokens
```

### 5.3 Auth Middleware

```python
@require_auth
def my_endpoint():
    user = g.current_user  # injected by middleware
    # user_id available for all repository calls
```

Applied to all `/api/graph/*`, `/api/simulation/*`, `/api/report/*` endpoints. Auth endpoints (`/api/auth/*`) and health check are excluded.

### 5.4 Trial Enforcement Middleware

```python
@require_active_plan
def create_project():
    # Checks: user.plan != 'trial' OR user.trial_ends_at > NOW()
    # Returns 403 with {error: "trial_expired", trial_ends_at: "..."} if expired
    # Read-only access to existing data is always allowed
```

Applied to project-creating and simulation-starting endpoints only.

### 5.5 CSRF Protection

Since JWT is in httpOnly cookies (browser auto-sends), we use the **double-submit cookie pattern**:
- On login, server sets a `csrf_token` cookie (NOT httpOnly — JS-readable)
- Frontend reads this cookie and sends it as `X-CSRF-Token` header on every mutating request (POST/PUT/DELETE)
- Server middleware verifies the header matches the cookie

### 5.6 Frontend Auth

- Vue Router navigation guards: redirect to `/login` if no valid token
- Axios interceptor: attach Bearer token + CSRF token to every request, auto-refresh on 401
- Auth store (Pinia): `user`, `isAuthenticated`, `isTrialExpired`, `trialDaysLeft` state
- Protected routes: all routes except `/`, `/login`, `/signup`, `/landing`

## 6. Session Resume System

Users can leave and come back to any project at any step.

### 6.1 step_data JSON shapes (validated by Pydantic):

```python
# Step 1 (Graph Build)
{
    "ontology_status": "completed",     # pending | generating | completed | failed
    "graph_build_status": "completed",  # pending | building | completed | failed
    "node_count": 42,
    "edge_count": 87,
    "task_id": "uuid"                   # references tasks table
}

# Step 2 (Env Setup)
{
    "simulation_id": "uuid",            # references simulations table
    "profile_status": "completed",
    "config_status": "completed",
    "task_id": "uuid"
}

# Step 3 (Simulation)
{
    "simulation_id": "uuid",
    "task_id": "uuid"
}

# Step 4 (Report)
{
    "report_id": "uuid",               # references reports table
    "task_id": "uuid"
}

# Step 5 (Interaction)
{
    "report_id": "uuid",
    "active_chat_session_ids": ["uuid1", "uuid2"]
}
```

### 6.2 Resume behavior per step:

| Step | On Resume |
|------|-----------|
| 1 - Graph Build | If ontology completed: show ontology editor. If graph completed: show graph viz. If failed/running: check task status. |
| 2 - Env Setup | Load simulation record, show generated profiles and config. |
| 3 - Simulation | If `status=running` AND `process_pid` is alive: reconnect to live stream. If `status=running` AND process dead: mark failed, offer restart. If completed: show results. |
| 4 - Report | If `status=generating`: show completed sections + "still generating" indicator. If completed: show full report. |
| 5 - Interaction | Load chat sessions and message history. Resume conversation. |

### 6.3 Startup recovery:

On server boot, scan for stale running states:
```python
def recover_stale_tasks():
    # Find tasks stuck in 'running' status
    stale_tasks = TaskRepository.find_by_status('running')
    for task in stale_tasks:
        task.status = 'failed'
        task.error = 'Server restarted during execution. Please retry.'

    # Find simulations stuck in 'running' with dead PIDs
    stale_sims = SimulationRepository.find_by_status('running')
    for sim in stale_sims:
        if sim.process_pid and not is_pid_alive(sim.process_pid):
            sim.status = 'failed'
            sim.error = 'Simulation process terminated unexpectedly.'
```

### 6.4 Dashboard view:

Users land on a dashboard showing their projects with status badges:
```
[Graph Building ●] Project: GPT-5 Impact Analysis — Step 1/5
[Completed ✓]      Project: Climate Policy Simulation — Step 5/5
[Simulation ▶]     Project: Election Prediction 2026 — Step 3/5
```

Clicking any project resumes from where they left off.

## 7. Error Handling

### 7.1 Remove stack traces from production responses

Replace all existing `traceback.format_exc()` returns with sanitized error responses:

```python
# Before (current - INSECURE)
return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()})

# After (production)
logger.error(f"Endpoint failed: {traceback.format_exc()}")  # log full trace
return jsonify({"success": False, "error": "Internal server error", "code": "INTERNAL_ERROR"}), 500
```

### 7.2 Centralized error handler

```python
@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, AuthError): return jsonify(error=str(e)), 401
    if isinstance(e, ForbiddenError): return jsonify(error=str(e)), 403
    if isinstance(e, NotFoundError): return jsonify(error=str(e)), 404
    if isinstance(e, ValidationError): return jsonify(error=str(e)), 422
    logger.error(f"Unhandled: {traceback.format_exc()}")
    return jsonify(error="Internal server error"), 500
```

## 8. Migration Order

Each step is a working commit. The app remains functional throughout.

| Step | What | Files Changed |
|------|------|--------------|
| 1 | Add SQLAlchemy + Alembic, create all DB models, configure connection pooling | New: `db.py`, `models/db_models.py`, `repositories/`, `alembic/` |
| 2 | Add PostgreSQL to Railway, run initial migration | New: `alembic.ini`, migration files |
| 3 | Implement TaskRepository (replace in-memory TaskManager) | New: `repositories/task_repo.py`. Modified: all task-creating code |
| 4 | Implement UserRepository + auth endpoints + refresh_tokens + CSRF | New: `api/auth.py`, `repositories/user_repo.py` |
| 5 | Add auth middleware + user_id checks to ALL existing endpoints simultaneously | Modified: `api/graph.py`, `api/simulation.py`, `api/report.py` |
| 6 | Frontend auth (login/signup pages, route guards, Axios interceptor, CSRF) | New: `views/Login.vue`, `views/Signup.vue`, `store/auth.js` |
| 7 | Migrate ProjectRepository (replace file-based project model) | Modified: `models/project.py` → `repositories/project_repo.py` |
| 8 | Migrate SimulationRepository + SimulationManager + simulation_actions | Modified: `services/simulation_runner.py`, `services/simulation_manager.py` |
| 9 | Migrate ReportRepository + report_sections + report_logs | Modified: `services/report_agent.py` |
| 10 | Migrate ChatRepository (new — currently no persistence) | New: `repositories/chat_repo.py` |
| 11 | Add dashboard view, project resume logic, startup recovery | New: `views/Dashboard.vue` |
| 12 | Sanitize all error responses, add centralized error handler | Modified: all `api/*.py` files |
| 13 | Remove old file-based storage code, in-memory caches, cleanup | Delete: old JSON file handlers, TaskManager singleton |

**Note:** Steps 4+5 are combined logically — auth middleware and user_id data isolation are deployed together to avoid any window where auth exists but data is unprotected.

## 9. File Upload Storage

Railway's filesystem is ephemeral — files are lost on each deploy. Options:

**Chosen approach:** Use Railway's persistent volume mount (`/data`) for uploaded files. Simple, no external service needed. If scaling beyond one instance, migrate to S3/R2.

```python
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/data/uploads')
```

`seed_files` JSONB on projects stores: `[{filename, size, storage_path, uploaded_at}]`

## 10. New Dependencies

### Backend
```
sqlalchemy>=2.0
alembic>=1.13
psycopg2-binary>=2.9       # PostgreSQL driver
passlib[bcrypt]>=1.7        # password hashing
python-jose[cryptography]   # JWT tokens
authlib>=1.3                # Google OAuth
flask-limiter>=3.5          # rate limiting for login endpoint
```

### Frontend
```
pinia>=2.1                  # state management (if not already)
```

## 11. Environment Variables (new)

```env
# PostgreSQL (Railway provides DATABASE_URL automatically)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# JWT
JWT_SECRET_KEY=<random-64-char-string>
JWT_ACCESS_TOKEN_EXPIRES=900        # 15 minutes in seconds
JWT_REFRESH_TOKEN_EXPIRES=604800    # 7 days in seconds

# Google OAuth
GOOGLE_CLIENT_ID=<from-google-console>
GOOGLE_CLIENT_SECRET=<from-google-console>
GOOGLE_REDIRECT_URI=https://your-domain.com/api/auth/google/callback

# File storage
UPLOAD_FOLDER=/data/uploads
```

## 12. Security Considerations

- Passwords hashed with bcrypt (cost factor 12), minimum 8 characters
- JWT stored in httpOnly, Secure, SameSite=Lax cookies
- CSRF protection via double-submit cookie pattern
- CORS restricted to specific frontend origin (no more `*`)
- All repository methods require `user_id` — no way to access another user's data
- Stack traces removed from API error responses in production
- Refresh tokens stored in DB with rotation — old token revoked on each refresh
- Login endpoint rate limited (5 attempts/min per IP)
- Google OAuth state parameter to prevent CSRF
- Input validation via Pydantic on all endpoints
- Soft deletes for users with 30-day grace period

## 13. Success Criteria

- [ ] User can sign up with email/password and Google OAuth
- [ ] User can log in and see a dashboard of their projects
- [ ] User can create a new project and run the full 5-step workflow
- [ ] User can close the browser, come back later, and resume from where they left off
- [ ] Reports and chat sessions are persisted and loadable across sessions
- [ ] User A cannot see User B's data (verified by test)
- [ ] 14-day trial timer visible in UI, blocks new projects after expiry
- [ ] Server restart recovers gracefully (stale tasks marked failed)
- [ ] No stack traces in production API responses
- [ ] Login endpoint resistant to brute force (rate limited)
