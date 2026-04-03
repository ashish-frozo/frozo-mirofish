"""
One-click prediction orchestrator.
Runs all 5 steps automatically: ontology -> graph -> simulation -> report -> ready for interaction.
"""

import os
import uuid
import time
import threading
import traceback
from flask import Blueprint, request, jsonify, g
from ..middleware.auth import require_auth, require_active_plan
from ..db import get_db
from ..repositories.task_repo import TaskRepository
from ..repositories.project_repo import ProjectRepository
from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.predict')

predict_bp = Blueprint('predict', __name__)


@predict_bp.route('', methods=['POST'])
@require_active_plan
def start_prediction():
    """Start a one-click prediction (upload files + requirement)
    ---
    tags:
      - Predict
    security:
      - Bearer: []
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: files
        type: file
        required: true
        description: Document files to analyze
      - in: formData
        name: simulation_requirement
        type: string
        required: true
        description: What to predict / simulate
    responses:
      202:
        description: Prediction started
        schema:
          type: object
          properties:
            success: {type: boolean}
            data:
              type: object
              properties:
                task_id: {type: string}
                status: {type: string}
                message: {type: string}
      400:
        description: Missing files or simulation requirement
      500:
        description: Internal error
    """
    try:
        user = g.current_user
        user_id = user.id  # Keep as UUID, don't convert to string

        # Get form data
        files = request.files.getlist('files')
        simulation_requirement = request.form.get('simulation_requirement', '')

        if not files:
            return jsonify({"success": False, "error": "No files uploaded"}), 400
        if not simulation_requirement:
            return jsonify({"success": False, "error": "Please provide a simulation requirement"}), 400

        # Create prediction task
        with get_db() as session:
            task_repo = TaskRepository(session)
            task = task_repo.create(
                user_id=user_id,
                task_type="prediction",
                metadata={"simulation_requirement": simulation_requirement}
            )
            task_id = str(task.id)

        # Save uploaded files temporarily
        temp_dir = os.path.join(Config.UPLOAD_FOLDER, 'temp', task_id)
        os.makedirs(temp_dir, exist_ok=True)
        saved_files = []
        for f in files:
            filepath = os.path.join(temp_dir, f.filename)
            f.save(filepath)
            saved_files.append({"filename": f.filename, "path": filepath})

        # Launch background orchestration thread
        thread = threading.Thread(
            target=_run_prediction,
            args=(task_id, user_id, saved_files, simulation_requirement),
            daemon=True
        )
        thread.start()

        return jsonify({
            "success": True,
            "data": {
                "task_id": task_id,
                "status": "running",
                "message": "Prediction started"
            }
        }), 202

    except Exception as e:
        logger.error(f"Failed to start prediction: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@predict_bp.route('/<task_id>/status', methods=['GET'])
def get_prediction_status(task_id: str):
    """Poll prediction progress
    ---
    tags:
      - Predict
    description: Accepts JWT Bearer auth or X-Service-Key header.
    parameters:
      - in: path
        name: task_id
        type: string
        required: true
        description: Prediction task ID
    responses:
      200:
        description: Prediction status
        schema:
          type: object
          properties:
            success: {type: boolean}
            data:
              type: object
              properties:
                task_id: {type: string}
                status: {type: string, enum: [pending, running, completed, failed]}
                progress: {type: integer}
                message: {type: string}
                stage: {type: string}
                stages: {type: object}
                result: {type: object}
                error: {type: string}
      401:
        description: Authentication required
      404:
        description: Task not found
    """
    service_key = request.headers.get('X-Service-Key', '')
    has_valid_service_key = (
        service_key and Config.BETTAFISH_SERVICE_KEY
        and service_key == Config.BETTAFISH_SERVICE_KEY
    )
    if not has_valid_service_key:
        # Try JWT auth
        import jwt as _jwt
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({"success": False, "error": "Authentication required"}), 401
        try:
            _jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
        except Exception:
            return jsonify({"success": False, "error": "Invalid token"}), 401
    try:
        with get_db() as session:
            task_repo = TaskRepository(session)
            task = task_repo.get_by_id(task_id)

            if not task:
                return jsonify({"success": False, "error": "Task not found"}), 404

            metadata = task.metadata_ or {}
            return jsonify({
                "success": True,
                "data": {
                    "task_id": str(task.id),
                    "status": task.status,
                    "progress": task.progress,
                    "message": task.message,
                    "stage": metadata.get("stage", ""),
                    "stages": metadata.get("stages", {}),
                    "result": task.result or metadata.get("result_preview", {}),
                    "error": task.error,
                }
            })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@predict_bp.route('/<task_id>/cancel', methods=['POST'])
@require_auth
def cancel_prediction(task_id: str):
    """Cancel a running prediction."""
    try:
        with get_db() as session:
            task_repo = TaskRepository(session)
            task_repo.fail(task_id, error="Cancelled by user")
        return jsonify({"success": True, "message": "Prediction cancelled"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def _run_prediction(task_id: str, user_id: str, saved_files: list, simulation_requirement: str):
    """
    Background thread: orchestrates all 5 prediction steps.
    Updates task progress at each stage.
    """
    def update(stage: str, progress: int, message: str, stages: dict = None, result_preview: dict = None):
        try:
            from sqlalchemy.orm.attributes import flag_modified
            with get_db() as session:
                task_repo = TaskRepository(session)
                task = task_repo.get_by_id(task_id)
                if task and task.status == "failed":
                    raise Exception("Cancelled")
                if task:
                    # Build new metadata dict (replace, don't mutate in-place)
                    new_metadata = dict(task.metadata_ or {})
                    new_metadata["stage"] = stage
                    if stages:
                        new_metadata["stages"] = stages
                    if result_preview:
                        new_metadata["result_preview"] = result_preview
                    task.metadata_ = new_metadata
                    task.status = "running"
                    task.progress = progress
                    task.message = message
                    flag_modified(task, "metadata_")
                    session.flush()
        except Exception as e:
            if "Cancelled" in str(e):
                raise
            logger.warning(f"Progress update failed: {e}")

    stages = {}

    try:
        # ==================== STEP 1: Ontology + Graph Build ====================
        update("ontology", 5, "Generating ontology from documents...", stages)

        # Import services
        from ..services.text_processor import TextProcessor
        from ..services.ontology_generator import OntologyGenerator
        from ..services.graph_builder import GraphBuilderService

        # Process text from files
        file_paths = [f["path"] for f in saved_files]
        all_text = TextProcessor.extract_from_files(file_paths)

        # Generate ontology
        ontology_gen = OntologyGenerator()
        chunks = TextProcessor.split_text(all_text)
        ontology = ontology_gen.generate(chunks, simulation_requirement)

        # Create project in DB
        with get_db() as session:
            proj_repo = ProjectRepository(session)
            project = proj_repo.create(
                user_id=user_id,
                name=simulation_requirement[:100],
                simulation_requirement=simulation_requirement,
            )
            project.ontology = ontology if isinstance(ontology, dict) else {"raw": str(ontology)}
            # Save prediction task_id so dashboard can route back to progress view
            step_data = dict(project.step_data or {})
            step_data["prediction_task_id"] = task_id
            project.step_data = step_data
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(project, "step_data")
            project.extracted_text = all_text
            project.status = "ontology_generated"
            session.flush()
            project_id = str(project.id)

        stages["ontology"] = {"status": "completed"}
        update("graph_build", 15, "Building knowledge graph...", stages)

        # Build graph using the service's existing methods
        builder = GraphBuilderService()
        graph_id = builder.create_graph(simulation_requirement[:80])
        builder.set_ontology(graph_id, ontology)

        # Add text in batches
        builder.add_text_batches(graph_id, chunks)
        graph_info = builder._get_graph_info(graph_id)

        # Update project with graph_id
        with get_db() as session:
            proj_repo = ProjectRepository(session)
            project = proj_repo.get_by_id(project_id)
            if project:
                proj_repo.update(project, graph_id=graph_id, status="graph_completed", current_step=2)

        stages["graph_build"] = {"status": "completed", "stats": {
            "nodes": graph_info.node_count,
            "edges": graph_info.edge_count,
            "graph_id": graph_id,
        }}
        update("env_setup", 30, "Setting up simulation environment...", stages, result_preview={"graph_id": graph_id, "project_id": project_id})

        # ==================== STEP 2: Simulation Setup ====================
        from ..services.simulation_manager import SimulationManager
        from ..repositories.simulation_repo import SimulationRepository

        manager = SimulationManager()
        state = manager.create_simulation(
            project_id=project_id,
            graph_id=graph_id,
            enable_twitter=True,
            enable_reddit=True,
        )
        simulation_id = state.simulation_id

        # Sync to DB
        with get_db() as session:
            sim_repo = SimulationRepository(session)
            db_sim = sim_repo.create(project_id=project_id)
            sim_repo.update(str(db_sim.id), simulation_id=simulation_id)

        update("env_setup", 35, "Generating agent profiles...", stages)

        # Prepare simulation (entity reading, profile generation, config generation)
        manager.prepare_simulation(
            simulation_id=simulation_id,
            simulation_requirement=simulation_requirement,
            document_text=all_text,
        )

        stages["env_setup"] = {"status": "completed"}
        update("simulation", 45, "Starting simulation...", stages)

        # ==================== STEP 3: Run Simulation ====================
        from ..services.simulation_runner import SimulationRunner

        # Update project status to simulating
        with get_db() as session:
            proj_repo = ProjectRepository(session)
            project = proj_repo.get_by_id(project_id)
            if project:
                project.status = "simulating"
                project.current_step = 3
                session.flush()

        SimulationRunner.start_simulation(simulation_id)

        # Poll for simulation completion
        while True:
            time.sleep(5)
            run_state = SimulationRunner.get_run_state(simulation_id)
            if not run_state:
                break

            status = run_state.runner_status.value if hasattr(run_state.runner_status, 'value') else str(run_state.runner_status)
            current_round = run_state.current_round
            total_rounds = run_state.total_rounds

            if total_rounds > 0:
                sim_progress = 45 + int((current_round / total_rounds) * 25)
            else:
                sim_progress = 50

            update("simulation", sim_progress, f"Simulation round {current_round}/{total_rounds}...", stages)

            if status in ("completed", "failed", "stopped"):
                break

            # Check if cancelled
            with get_db() as session:
                task = TaskRepository(session).get_by_id(task_id)
                if task and task.status == "failed":
                    SimulationRunner.stop_simulation(simulation_id)
                    return

        # Save simulation stats to project
        sim_rounds = run_state.total_rounds if run_state else 0
        with get_db() as session:
            proj_repo = ProjectRepository(session)
            project = proj_repo.get_by_id(project_id)
            if project:
                step_data = dict(project.step_data or {})
                step_data["rounds"] = sim_rounds
                step_data["simulation_id"] = simulation_id
                project.step_data = step_data
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(project, "step_data")
                session.flush()

        stages["simulation"] = {"status": "completed", "stats": {
            "rounds": sim_rounds,
            "total_actions": run_state.current_round if run_state else 0,
        }}
        update("report", 75, "Generating prediction report...", stages)

        # ==================== STEP 4: Report Generation ====================
        from ..services.report_agent import ReportAgent

        # Update project status to reporting
        with get_db() as session:
            proj_repo = ProjectRepository(session)
            project = proj_repo.get_by_id(project_id)
            if project:
                project.status = "reporting"
                project.current_step = 4
                session.flush()

        report_agent = ReportAgent(
            graph_id=graph_id,
            simulation_id=simulation_id,
            simulation_requirement=simulation_requirement,
        )

        report = report_agent.generate_report()

        report_id = report.report_id if report else None

        # Update project with simulation_id and report_id for navigation
        with get_db() as session:
            proj_repo = ProjectRepository(session)
            project = proj_repo.get_by_id(project_id)
            if project:
                step_data = dict(project.step_data or {})
                step_data["simulation_id"] = simulation_id
                step_data["report_id"] = report_id
                project.step_data = step_data
                project.status = "completed"
                project.current_step = 5
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(project, "step_data")
                session.flush()

        stages["report"] = {"status": "completed", "report_id": report_id}
        stages["interaction"] = {"status": "ready"}

        # ==================== SEND EMAIL NOTIFICATION ====================
        try:
            from ..services.email_service import send_report_email
            from ..repositories.user_repo import UserRepository

            with get_db() as session:
                user_repo = UserRepository(session)
                user = user_repo.get_by_id(user_id)
                if user and user.email:
                    markdown_content = report.markdown_content if report else None
                    send_report_email(
                        to_email=user.email,
                        user_name=user.name or '',
                        project_name=simulation_requirement[:100],
                        project_id=project_id,
                        markdown_content=markdown_content,
                    )
        except Exception as e:
            logger.warning(f"Failed to send report email: {e}")

        # ==================== COMPLETE ====================
        with get_db() as session:
            task_repo = TaskRepository(session)
            task_repo.complete(task_id, result={
                "project_id": project_id,
                "graph_id": graph_id,
                "simulation_id": simulation_id,
                "report_id": report_id,
                "stages": stages,
            })

        logger.info(f"Prediction complete: task={task_id}, project={project_id}")

    except Exception as e:
        if "Cancelled" in str(e):
            return
        logger.error(f"Prediction failed: {e}\n{traceback.format_exc()}")
        with get_db() as session:
            task_repo = TaskRepository(session)
            task_repo.fail(task_id, error=str(e))
    finally:
        # Clean up temp files
        import shutil
        temp_dir = os.path.join(Config.UPLOAD_FOLDER, 'temp', task_id)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# BettaFish Integration Endpoints
# ---------------------------------------------------------------------------

@predict_bp.route('/validation-result', methods=['POST'])
def receive_validation_result():
    """Webhook: receive validation result from BettaFish."""
    from ..middleware.service_auth import service_auth_required as _svc_auth

    # Manual auth check (can't stack decorators easily on this route)
    service_key = request.headers.get('X-Service-Key', '')
    if not Config.BETTAFISH_SERVICE_KEY or service_key != Config.BETTAFISH_SERVICE_KEY:
        return jsonify({"success": False, "error": "Invalid service key"}), 401

    from ..models.prediction_validation import PredictionValidationModel

    data = request.get_json(silent=True) or {}
    prediction_id = data.get("prediction_id")

    if not prediction_id:
        return jsonify({"success": False, "error": "prediction_id required"}), 400

    try:
        with get_db() as session:
            task_repo = TaskRepository(session)
            task = task_repo.get_by_id(prediction_id)
            user_id = task.user_id if task else None

            validation = PredictionValidationModel(
                prediction_task_id=prediction_id,
                user_id=user_id,
                bettafish_prediction_id=data.get("bettafish_prediction_id"),
                accuracy_score=data.get("accuracy_score"),
                actual_sentiment=data.get("actual_sentiment"),
                actual_trajectory=data.get("actual_trajectory"),
                per_prediction=data.get("per_prediction"),
                validated_at=data.get("validated_at"),
            )
            session.add(validation)

        return jsonify({"success": True}), 200
    except Exception as e:
        logger.error(f"Failed to store validation result: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@predict_bp.route('/accuracy', methods=['GET'])
@require_auth
def get_accuracy():
    """Get prediction accuracy dashboard data."""
    from ..models.prediction_validation import PredictionValidationModel

    try:
        with get_db() as session:
            validations = session.query(PredictionValidationModel).filter(
                PredictionValidationModel.user_id == g.current_user.id
            ).order_by(PredictionValidationModel.created_at.desc()).all()

            completed = [v for v in validations if v.accuracy_score is not None]

            overall = (
                sum(v.accuracy_score for v in completed) / len(completed)
                if completed else 0
            )

            return jsonify({
                "success": True,
                "data": {
                    "overall_accuracy": round(overall),
                    "total_predictions": len(validations),
                    "validated_count": len(completed),
                    "recent_validations": [
                        {
                            "prediction_task_id": str(v.prediction_task_id),
                            "accuracy_score": v.accuracy_score,
                            "validated_at": v.validated_at.isoformat() if v.validated_at else None,
                            "per_prediction": v.per_prediction,
                        }
                        for v in completed[:10]
                    ],
                }
            })
    except Exception as e:
        logger.error(f"Failed to get accuracy data: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
