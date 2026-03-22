"""
Crawl Import API — accepts BettaFish crawl bundles for prediction.
"""
import os
import threading
from flask import Blueprint, request, jsonify, g
from ..middleware.service_auth import service_auth_required
from ..services.crawl_seed_transformer import CrawlSeedTransformer
from ..config import Config
from ..db import get_db
from ..repositories.user_repo import UserRepository
from ..repositories.task_repo import TaskRepository
from ..utils.logger import get_logger

logger = get_logger('mirofish.crawl_import')

crawl_import_bp = Blueprint('crawl_import', __name__)

# Cache service account user_id in memory
_service_user_id = None
_service_user_lock = threading.Lock()

SERVICE_ACCOUNT_EMAIL = "service@bettafish.internal"


def _get_or_create_service_user():
    """Get or create the BettaFish service account user."""
    global _service_user_id

    if _service_user_id:
        return _service_user_id

    with _service_user_lock:
        if _service_user_id:
            return _service_user_id

        with get_db() as session:
            repo = UserRepository(session)
            user = repo.get_by_email(SERVICE_ACCOUNT_EMAIL)

            if not user:
                from ..models.db_models import UserModel, utcnow
                from datetime import timedelta
                user = UserModel(
                    email=SERVICE_ACCOUNT_EMAIL,
                    name="BettaFish Service",
                    password_hash="",
                    auth_provider="service",
                    plan="enterprise",
                    trial_ends_at=utcnow() + timedelta(days=36500),
                )
                session.add(user)
                session.flush()
                logger.info(f"Created BettaFish service account: {user.id}")

            _service_user_id = user.id
            return _service_user_id


@crawl_import_bp.route('/from-crawl', methods=['POST'])
@service_auth_required
def predict_from_crawl():
    """Start a prediction from BettaFish crawl data.

    POST /api/predict/from-crawl
    Headers: X-Service-Key: <shared secret>
    Body: {"crawl_bundle": {...}, "callback_url": "..."}
    Returns: {"success": true, "data": {"task_id": "...", "status": "running"}}
    """
    data = request.get_json(silent=True) or {}
    crawl_bundle = data.get("crawl_bundle")
    callback_url = data.get("callback_url")

    if not crawl_bundle:
        return jsonify({"success": False, "error": "crawl_bundle is required"}), 400

    # Transform the bundle
    transformer = CrawlSeedTransformer()
    transformed = transformer.transform(crawl_bundle)

    # Get service account user
    service_user_id = _get_or_create_service_user()

    # Create task
    with get_db() as session:
        task_repo = TaskRepository(session)
        task = task_repo.create(
            user_id=service_user_id,
            task_type="prediction",
            metadata={
                "service_origin": "bettafish",
                "simulation_requirement": transformed["simulation_requirement"],
                "calibration_data": transformed.get("calibration_data", []),
            }
        )
        task_id = str(task.id)

    # Write seed text to a temp file for the existing pipeline
    temp_dir = os.path.join(Config.UPLOAD_FOLDER, 'temp', task_id)
    os.makedirs(temp_dir, exist_ok=True)
    seed_path = os.path.join(temp_dir, "crawl_seed.md")
    with open(seed_path, 'w', encoding='utf-8') as f:
        f.write(transformed["seed_text"])

    saved_files = [{"filename": "crawl_seed.md", "path": seed_path}]

    # Run prediction in background thread (reuses existing _run_prediction)
    from .predict import _run_prediction
    thread = threading.Thread(
        target=_run_prediction_from_crawl,
        args=(task_id, service_user_id, saved_files, transformed, callback_url),
        daemon=True,
    )
    thread.start()

    return jsonify({
        "success": True,
        "data": {
            "task_id": task_id,
            "status": "running",
            "message": "Prediction started from BettaFish crawl data",
        }
    }), 202


def _run_prediction_from_crawl(task_id, user_id, saved_files, transformed_data, callback_url=None):
    """Run prediction with callback support."""
    import httpx
    from .predict import _run_prediction

    try:
        # Run the standard prediction pipeline
        _run_prediction(task_id, user_id, saved_files, transformed_data["simulation_requirement"])

        # POST callback if provided
        if callback_url:
            with get_db() as session:
                task_repo = TaskRepository(session)
                task = task_repo.get_by_id(task_id)
                result = task.result if task else {}

            try:
                with httpx.Client(timeout=30) as client:
                    for attempt in range(3):
                        try:
                            resp = client.post(callback_url, json={
                                "task_id": task_id,
                                "status": "completed",
                                "result": result,
                            })
                            if resp.status_code < 400:
                                break
                        except httpx.HTTPError:
                            import time
                            time.sleep(5 * (2 ** attempt))
            except Exception as e:
                logger.warning(f"Callback to {callback_url} failed: {e}")

    except Exception as e:
        logger.error(f"Prediction from crawl failed for task {task_id}: {e}")
