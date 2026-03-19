# Phase 2: Data Migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Replace all file-based storage (ProjectManager, SimulationManager, ReportManager) and in-memory storage (TaskManager) with PostgreSQL repositories. Add project list API for the dashboard. Wire user_id through all operations for data isolation.

**Architecture:** Each Manager gets a corresponding Repository. API endpoints are updated to use repositories instead of file managers. user_id from `g.current_user` is passed through all operations. File uploads remain on disk (Railway persistent volume) with metadata in DB.

**Spec:** `docs/superpowers/specs/2026-03-19-database-multitenancy-auth-design.md`

---

## Task 1: Project Repository + API Migration

Replace `ProjectManager` (file-based) with `ProjectRepository` (PostgreSQL).

**Files:**
- Create: `backend/app/repositories/project_repo.py`
- Modify: `backend/app/api/graph.py` — replace all `ProjectManager` calls with `ProjectRepository`
- Modify: `backend/app/models/project.py` — keep dataclass for backward compat, mark deprecated

**Key changes in graph.py:**
- `ProjectManager.create_project()` → `ProjectRepository.create(user_id, name, requirement)`
- `ProjectManager.get_project()` → `ProjectRepository.get_by_id(project_id, user_id)`
- `ProjectManager.list_projects()` → `ProjectRepository.list_by_user(user_id)`
- `ProjectManager.save_project()` → `ProjectRepository.update(project_id, user_id, **fields)`
- `ProjectManager.save_extracted_text()` → `ProjectRepository.update(project_id, user_id, extracted_text=text)`
- `ProjectManager.save_file_to_project()` → files still on disk, metadata in DB `seed_files` JSONB
- Ontology result saved to `projects.ontology` column instead of project.json

**Important:** `g.current_user.id` must be passed as `user_id` to every repository call. This enforces data isolation.

---

## Task 2: Task Repository Integration

Replace in-memory `TaskManager` singleton with the already-built `TaskRepository`.

**Files:**
- Modify: `backend/app/api/graph.py` — replace `TaskManager.create_task()` etc. with `TaskRepository`
- Modify: `backend/app/api/simulation.py` — same replacement
- Modify: `backend/app/api/report.py` — same replacement
- Modify: `backend/app/__init__.py` — add startup recovery call

**Key changes:**
- `task_manager.create_task()` → `TaskRepository(session).create(user_id, task_type)`
- `task_manager.get_task()` → `TaskRepository(session).get_by_id(task_id)`
- `task_manager.update_task()` → `TaskRepository(session).update_progress(task_id, ...)`
- On startup: call `TaskRepository.recover_stale()` to mark orphaned tasks as failed

---

## Task 3: Simulation Repository + API Migration

Replace `SimulationManager` file-based state with `SimulationRepository`.

**Files:**
- Create: `backend/app/repositories/simulation_repo.py`
- Modify: `backend/app/api/simulation.py` — replace `SimulationManager` calls
- Modify: `backend/app/services/simulation_manager.py` — use repository for state persistence

**Key changes:**
- `SimulationManager.create_simulation()` → `SimulationRepository.create(project_id, ...)`
- `SimulationManager._save_simulation_state()` → `SimulationRepository.update(sim_id, ...)`
- `SimulationManager._load_simulation_state()` → `SimulationRepository.get_by_id(sim_id)`
- Agent profiles saved to `agent_profiles` table instead of JSON files
- Simulation config saved to `simulations.config` JSONB instead of file
- Per-round summaries saved to `simulation_round_summaries` table

**Note:** Profile files (reddit_profiles.json, twitter_profiles.csv) are still needed by OASIS subprocess. Keep writing them to disk for OASIS, but also save to DB for persistence.

---

## Task 4: Report Repository + API Migration

Replace `ReportManager` file-based storage with `ReportRepository`.

**Files:**
- Create: `backend/app/repositories/report_repo.py`
- Modify: `backend/app/api/report.py` — replace `ReportManager` calls
- Modify: `backend/app/services/report_agent.py` — use repository for saving

**Key changes:**
- `ReportManager.save_report()` → `ReportRepository.save(report_data)`
- `ReportManager.get_report()` → `ReportRepository.get_by_id(report_id)`
- `ReportManager.save_section()` → `ReportRepository.save_section(report_id, index, content)`
- `ReportManager.update_progress()` → `ReportRepository.update_progress(report_id, ...)`
- `ReportManager.get_agent_log()` → `ReportRepository.get_logs(report_id, 'agent')`
- `ReportManager.get_console_log()` → `ReportRepository.get_logs(report_id, 'console')`
- Report logs saved to `report_logs` table instead of JSONL files
- Sections saved to `report_sections` table instead of individual .md files

---

## Task 5: Chat Repository (New Persistence)

Add chat session and message persistence (currently not saved at all).

**Files:**
- Create: `backend/app/repositories/chat_repo.py`
- Modify: `backend/app/api/report.py` (chat endpoints) — save/load from DB

**Key changes:**
- On chat start: create `chat_sessions` row
- On each message: save to `chat_messages` table
- On resume: load conversation history from DB
- Support both report_agent and sim_agent chat types

---

## Task 6: Dashboard API + Frontend Integration

Add project list API and wire the dashboard to real data.

**Files:**
- Create: `backend/app/api/dashboard.py` — new blueprint with project list, stats
- Modify: `frontend/src/views/Dashboard.vue` — fetch and display real projects
- Modify: `frontend/src/api/index.js` or create `frontend/src/api/projects.js`

**Endpoints:**
- `GET /api/projects` — list user's projects with status, step, dates
- `GET /api/projects/:id/resume` — get step_data for resuming

---

## Task 7: Cleanup — Remove Old File-Based Code

Remove deprecated file managers and in-memory caches.

**Files:**
- Delete/gut: `backend/app/models/project.py` (ProjectManager)
- Delete/gut: `backend/app/models/task.py` (TaskManager singleton)
- Remove: file-based save/load methods from SimulationManager
- Remove: ReportManager class from report_agent.py
- Clean up: unused imports across all modified files
