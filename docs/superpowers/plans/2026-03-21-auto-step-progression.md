# Auto Step Progression Plan

> Deferred — implement after end-to-end flow is validated.

**Goal:** Users upload a document + enter a prediction requirement, click ONE button, and the system automatically progresses through all 5 steps without manual intervention. The user watches the progress and can interact at step 5.

## Current Flow (Too Many Clicks)

```
User uploads file → clicks "Generate" → waits →
  clicks "Build Graph" → waits →
    manually goes to Step 2 → clicks "Create Simulation" →
      clicks "Prepare" → waits →
        manually goes to Step 3 → clicks "Start Simulation" → waits →
          manually goes to Step 4 → clicks "Generate Report" → waits →
            manually goes to Step 5 → can interact
```

**~8-10 manual clicks across 5 steps.** Users don't know what to click next.

## Target Flow (One Click)

```
User uploads file + enters requirement → clicks "Predict" →

  [Auto] Step 1: Ontology → Graph Build → ✓
  [Auto] Step 2: Entity Read → Profile Gen → Sim Config → ✓
  [Auto] Step 3: Simulation Runs (Twitter + Reddit) → ✓
  [Auto] Step 4: Report Generation → ✓
  [Auto] Step 5: Ready for Interaction ← User takes over here
```

**1 click.** User watches a live progress dashboard while the system works.

## Design

### Progress Dashboard (replaces manual step clicking)

```
┌──────────────────────────────────────────────────────┐
│  Predicting: "GPT-5 Impact Analysis"                 │
│                                                      │
│  ████████████████████░░░░░░░░░░░░░  62%              │
│                                                      │
│  ✓ Step 1: Knowledge Graph    42 entities, 78 edges  │
│  ✓ Step 2: Agent Profiles     15 agents configured   │
│  ▶ Step 3: Simulation         Round 3/5 running...   │
│  ○ Step 4: Report             Waiting...             │
│  ○ Step 5: Interaction        Waiting...             │
│                                                      │
│  ┌─ Live Log ────────────────────────────────────┐   │
│  │ [14:23:01] Agent "Sarah Chen" posted on Twitter│  │
│  │ [14:23:03] Agent "Prof Williams" replied...    │  │
│  │ [14:23:05] Round 3 complete: 12 actions        │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  [Cancel]                              [View Graph]  │
└──────────────────────────────────────────────────────┘
```

### Backend: Orchestrator Endpoint

New endpoint: `POST /api/predict` — single entry point that orchestrates all 5 steps.

```python
@graph_bp.route('/predict', methods=['POST'])
@require_auth
def start_prediction():
    """
    One-click prediction: upload files + requirement → auto-run all 5 steps.
    Returns a prediction_task_id that the frontend polls for progress.
    """
    # 1. Create project (same as ontology/generate)
    # 2. Spawn background thread that runs:
    #    a. Generate ontology
    #    b. Build graph
    #    c. Create simulation + prepare
    #    d. Start simulation + wait for completion
    #    e. Generate report
    #    f. Mark as ready for interaction
    # 3. Return prediction_task_id immediately
```

Progress tracking via the existing task system:
```python
# Task progress updates at each stage:
task.update(stage="graph_build", progress=15, message="Building knowledge graph...")
task.update(stage="env_setup", progress=30, message="Generating 15 agent profiles...")
task.update(stage="simulation", progress=50, message="Simulation round 3/5...")
task.update(stage="report", progress=80, message="Writing section 2/4...")
task.update(stage="complete", progress=100, message="Ready for interaction")
```

### Frontend: Prediction Progress View

New view: `PredictionProgress.vue` — replaces the manual step-by-step workflow for new predictions.

**Route:** `/predict/:taskId`

**Behavior:**
1. After clicking "Predict" on upload page, redirect to `/predict/:taskId`
2. Poll `GET /api/predict/:taskId/status` every 2 seconds
3. Show progress bar + step checklist + live log
4. When complete, show "Explore Results" button → navigates to Step 5 interaction
5. If error at any step, show error with "Retry from Step X" option

### API Changes

| Endpoint | Purpose |
|----------|---------|
| `POST /api/predict` | Start one-click prediction (upload + all steps) |
| `GET /api/predict/:taskId/status` | Poll progress (returns stage, progress %, step statuses, log) |
| `POST /api/predict/:taskId/cancel` | Cancel running prediction |
| `POST /api/predict/:taskId/retry` | Retry from failed step |

### Status Response Shape

```json
{
  "task_id": "uuid",
  "status": "running",
  "progress": 62,
  "current_stage": "simulation",
  "stages": {
    "ontology": {"status": "completed", "duration_seconds": 35},
    "graph_build": {"status": "completed", "duration_seconds": 120, "stats": {"nodes": 42, "edges": 78}},
    "env_setup": {"status": "completed", "duration_seconds": 45, "stats": {"agents": 15}},
    "simulation": {"status": "running", "progress": 60, "stats": {"round": 3, "total_rounds": 5}},
    "report": {"status": "pending"},
    "interaction": {"status": "pending"}
  },
  "recent_logs": [
    {"time": "14:23:01", "message": "Agent 'Sarah Chen' posted on Twitter"},
    {"time": "14:23:03", "message": "Agent 'Prof Williams' replied..."}
  ],
  "result": null
}
```

### Existing Step Views (Keep for Resume/Manual)

The existing Step1-5 components still work for:
- **Resuming** a paused/failed prediction at a specific step
- **Power users** who want manual control
- **Viewing details** of a completed step

But the **default new prediction flow** uses the auto-progression.

## Implementation Tasks

| Task | What | Effort |
|------|------|--------|
| 1 | Create `POST /api/predict` orchestrator endpoint | 3h |
| 2 | Create `GET /api/predict/:taskId/status` with stage tracking | 1h |
| 3 | Create `PredictionProgress.vue` with progress bar + step list + log | 3h |
| 4 | Update upload page to call `/api/predict` instead of `/api/graph/ontology/generate` | 1h |
| 5 | Add cancel + retry endpoints | 1h |
| 6 | Connect "Explore Results" button to Step 5 interaction view | 30min |
| 7 | Add live log streaming (SSE or polling) | 2h |
| **Total** | | **~11.5h** |

## Error Handling

| Step Fails | Behavior |
|------------|----------|
| Ontology generation | Show error, "Retry" button restarts from step 1 |
| Graph build | Show error with partial graph stats, "Retry" resumes graph build |
| Simulation prep | Show error, "Retry" regenerates profiles/config |
| Simulation run | Show error with partial results, "Retry" or "Use Partial Results" |
| Report generation | Show error, "Retry" or "Skip to Interaction" (can chat without report) |

## UX Principles

1. **Show progress, not emptiness** — always show what's happening
2. **Time estimates** — "~3 minutes remaining" based on step timing
3. **Interruptible** — user can cancel anytime, data is preserved
4. **Resumable** — if user navigates away, they can resume from dashboard
5. **Transparent** — live log shows exactly what agents are doing
6. **Celebratory** — confetti/animation when prediction completes (optional)
