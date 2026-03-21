# Plan-Based Simulation Limits — Implementation Plan

> Deferred — implement after end-to-end flow is validated.

**Goal:** Tie simulation parameters (rounds, hours, agents) to the user's subscription plan so cheaper tiers get lighter simulations and paid tiers get deeper analysis.

## Limit Matrix

| Parameter | Trial/Starter | Pro | Enterprise |
|-----------|--------------|-----|-----------|
| Max rounds | 5 | 10 | 20 |
| Simulation hours | 24 | 72 | 168 |
| Agents per hour (max) | 15 | 30 | 50 |
| Minutes per round | 120 | 60 | 30 |
| Simulations per month | 5 | 20 | Unlimited |

## Where to Implement

1. **`backend/app/api/billing.py`** — `PLAN_LIMITS` dict already exists, add simulation params:
```python
PLAN_LIMITS = {
    'trial':      {'simulations_per_month': 3, 'max_rounds': 5, 'sim_hours': 24, 'agents_per_hour_max': 15, 'minutes_per_round': 120},
    'starter':    {'simulations_per_month': 5, 'max_rounds': 5, 'sim_hours': 24, 'agents_per_hour_max': 15, 'minutes_per_round': 120},
    'pro':        {'simulations_per_month': 20, 'max_rounds': 10, 'sim_hours': 72, 'agents_per_hour_max': 30, 'minutes_per_round': 60},
    'enterprise': {'simulations_per_month': 999, 'max_rounds': 20, 'sim_hours': 168, 'agents_per_hour_max': 50, 'minutes_per_round': 30},
}
```

2. **`backend/app/services/simulation_config_generator.py`** — Accept plan limits as input, override LLM-generated config if it exceeds plan caps:
```python
def generate_config(self, ..., plan_limits: dict = None):
    config = self._llm_generate_config(...)
    if plan_limits:
        config.total_simulation_hours = min(config.total_simulation_hours, plan_limits['sim_hours'])
        config.minutes_per_round = max(config.minutes_per_round, plan_limits['minutes_per_round'])
        config.agents_per_hour_max = min(config.agents_per_hour_max, plan_limits['agents_per_hour_max'])
    return config
```

3. **`backend/app/api/simulation.py`** — In `prepare_simulation`, fetch user's plan limits and pass to config generator:
```python
from ..api.billing import PLAN_LIMITS
plan = g.current_user.plan
limits = PLAN_LIMITS.get(plan, PLAN_LIMITS['trial'])
```

4. **`backend/app/config.py`** — `OASIS_DEFAULT_MAX_ROUNDS` becomes a ceiling enforced per-plan, not a global default.

5. **Frontend** — Show plan limits on the simulation setup UI. "Pro plan: up to 72h simulation, 30 agents" badge.

## Estimated Effort
- 2-3 hours
- No new files, just modifications to existing billing + simulation code
