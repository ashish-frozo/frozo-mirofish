"""Admin-only endpoints. Gated by Config.ADMIN_EMAILS."""

from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload

from ..db import get_db
from ..middleware.auth import require_admin
from ..models.db_models import TaskModel, UserModel
from ..services import cost_tracker
from ..utils.logger import get_logger

logger = get_logger('mirofish.admin')

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/predictions/costs', methods=['GET'])
@require_admin
def list_prediction_costs():
    """List recent prediction tasks with estimated LLM cost.

    Query params:
      - limit (int, default 50, max 500)
      - user_email (str, optional): filter to one user
      - include_running (bool, default true): include tasks still in flight
        (cost is read live from Redis for those; completed tasks read from
        the persisted task metadata).
    ---
    tags: [Admin]
    security:
      - Bearer: []
    parameters:
      - in: query
        name: limit
        type: integer
      - in: query
        name: user_email
        type: string
      - in: query
        name: include_running
        type: boolean
    responses:
      200: { description: "List of prediction cost rows" }
      401: { description: "Auth required" }
      403: { description: "Admin only" }
    """
    try:
        limit = min(max(int(request.args.get('limit', 50)), 1), 500)
    except ValueError:
        limit = 50
    user_email = (request.args.get('user_email') or '').strip().lower() or None
    include_running = request.args.get('include_running', 'true').lower() != 'false'

    with get_db() as session:
        q = (
            session.query(TaskModel)
            .filter(TaskModel.type == 'prediction')
            .options(joinedload(TaskModel.user))
        )
        if not include_running:
            q = q.filter(TaskModel.status.in_(['completed', 'failed']))
        q = q.order_by(TaskModel.created_at.desc()).limit(limit)
        tasks = q.all()

        if user_email:
            tasks = [t for t in tasks if (t.user and t.user.email.lower() == user_email)]

        rows = []
        totals = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0, "cost_usd": 0.0}
        for t in tasks:
            # Prefer persisted metadata.cost (authoritative after completion);
            # fall back to live Redis counters for running tasks.
            md = t.metadata_ or {}
            cost = md.get("cost") if md else None
            if not cost and t.status == "running":
                cost = cost_tracker.get(str(t.id))
            if not cost:
                cost = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0, "cost_usd": 0.0}

            rows.append({
                "task_id": str(t.id),
                "status": t.status,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "user_id": str(t.user_id),
                "user_email": t.user.email if t.user else None,
                "user_name": t.user.name if t.user else None,
                "simulation_requirement": (md.get("simulation_requirement") or "")[:200],
                "calls": int(cost.get("calls", 0)),
                "prompt_tokens": int(cost.get("prompt_tokens", 0)),
                "completion_tokens": int(cost.get("completion_tokens", 0)),
                "cost_usd": round(float(cost.get("cost_usd", 0.0)), 6),
            })
            totals["prompt_tokens"] += rows[-1]["prompt_tokens"]
            totals["completion_tokens"] += rows[-1]["completion_tokens"]
            totals["calls"] += rows[-1]["calls"]
            totals["cost_usd"] += rows[-1]["cost_usd"]

        totals["cost_usd"] = round(totals["cost_usd"], 4)

    return jsonify({
        "success": True,
        "data": {
            "rows": rows,
            "totals": totals,
            "count": len(rows),
        },
    })


@admin_bp.route('/predictions/<task_id>/cost', methods=['GET'])
@require_admin
def get_prediction_cost(task_id: str):
    """Detailed cost breakdown for a single prediction.
    ---
    tags: [Admin]
    """
    with get_db() as session:
        task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not task:
            return jsonify({"success": False, "error": "Task not found"}), 404

        md = task.metadata_ or {}
        persisted = md.get("cost") or {}
        live = cost_tracker.get(task_id)

        return jsonify({
            "success": True,
            "data": {
                "task_id": str(task.id),
                "status": task.status,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "simulation_requirement": md.get("simulation_requirement"),
                "persisted": persisted,
                "live_redis": live,
                "source_of_truth": "persisted" if task.status == "completed" else "live_redis",
            },
        })
