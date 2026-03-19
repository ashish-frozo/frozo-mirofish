"""
Graph-related API routes
Uses project context mechanism with server-side state persistence
"""

import os
import traceback
import threading
from flask import request, jsonify, g

from . import graph_bp
from ..config import Config
from ..services.ontology_generator import OntologyGenerator
from ..services.graph_builder import GraphBuilderService
from ..services.text_processor import TextProcessor
from ..utils.file_parser import FileParser
from ..utils.logger import get_logger
from ..models.task import TaskManager, TaskStatus
from ..repositories.project_repo import ProjectRepository
from ..db import get_db
from ..middleware.auth import require_auth

# Get logger
logger = get_logger('mirofish.api')


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _project_to_dict(project) -> dict:
    """Serialize a ProjectModel to the dict shape the frontend expects."""
    return {
        "project_id": str(project.id),
        "name": project.name,
        "status": project.status,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        "files": project.seed_files or [],
        "total_text_length": len(project.extracted_text) if project.extracted_text else 0,
        "ontology": project.ontology,
        "analysis_summary": project.analysis_summary,
        "graph_id": project.graph_id,
        "graph_build_task_id": project.step_data.get("graph_build_task_id") if project.step_data else None,
        "simulation_requirement": project.simulation_requirement,
        "chunk_size": project.chunk_size,
        "chunk_overlap": project.chunk_overlap,
        "error": project.step_data.get("error") if project.step_data else None,
    }


def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed"""
    if not filename or '.' not in filename:
        return False
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    return ext in Config.ALLOWED_EXTENSIONS


# ============== Project Management APIs ==============

@graph_bp.route('/project/<project_id>', methods=['GET'])
@require_auth
def get_project(project_id: str):
    """
    Get project details
    """
    session = g.db_session
    repo = ProjectRepository(session)
    user_id = g.current_user.id

    project = repo.get_by_id(project_id, user_id=user_id)

    if not project:
        return jsonify({
            "success": False,
            "error": f"Project not found: {project_id}"
        }), 404

    return jsonify({
        "success": True,
        "data": _project_to_dict(project)
    })


@graph_bp.route('/project/list', methods=['GET'])
@require_auth
def list_projects():
    """
    List all projects for the current user
    """
    session = g.db_session
    repo = ProjectRepository(session)
    user_id = g.current_user.id

    limit = request.args.get('limit', 50, type=int)
    projects = repo.list_by_user(user_id, limit=limit)

    return jsonify({
        "success": True,
        "data": [_project_to_dict(p) for p in projects],
        "count": len(projects)
    })


@graph_bp.route('/project/<project_id>', methods=['DELETE'])
@require_auth
def delete_project(project_id: str):
    """
    Delete a project
    """
    session = g.db_session
    repo = ProjectRepository(session)
    user_id = g.current_user.id

    success = repo.delete(project_id, user_id)

    if not success:
        return jsonify({
            "success": False,
            "error": f"Project not found or deletion failed: {project_id}"
        }), 404

    return jsonify({
        "success": True,
        "message": f"Project deleted: {project_id}"
    })


@graph_bp.route('/project/<project_id>/reset', methods=['POST'])
@require_auth
def reset_project(project_id: str):
    """
    Reset project status (for rebuilding the graph)
    """
    session = g.db_session
    repo = ProjectRepository(session)
    user_id = g.current_user.id

    project = repo.get_by_id(project_id, user_id=user_id)

    if not project:
        return jsonify({
            "success": False,
            "error": f"Project not found: {project_id}"
        }), 404

    # Reset to ontology generated state
    new_status = "ontology_generated" if project.ontology else "created"

    step_data = dict(project.step_data or {})
    step_data.pop("graph_build_task_id", None)
    step_data.pop("error", None)

    repo.update(
        project,
        status=new_status,
        graph_id=None,
        step_data=step_data,
    )

    return jsonify({
        "success": True,
        "message": f"Project reset: {project_id}",
        "data": _project_to_dict(project)
    })


# ============== API 1: Upload Files and Generate Ontology ==============

@graph_bp.route('/ontology/generate', methods=['POST'])
@require_auth
def generate_ontology():
    """
    API 1: Upload files, analyze and generate ontology definition

    Request format: multipart/form-data

    Parameters:
        files: Uploaded files (PDF/MD/TXT), multiple allowed
        simulation_requirement: Simulation requirement description (required)
        project_name: Project name (optional)
        additional_context: Additional notes (optional)

    Returns:
        {
            "success": true,
            "data": {
                "project_id": "...",
                "ontology": {
                    "entity_types": [...],
                    "edge_types": [...],
                    "analysis_summary": "..."
                },
                "files": [...],
                "total_text_length": 12345
            }
        }
    """
    try:
        logger.info("=== Starting ontology generation ===")

        session = g.db_session
        repo = ProjectRepository(session)
        user_id = g.current_user.id

        # Get parameters
        simulation_requirement = request.form.get('simulation_requirement', '')
        project_name = request.form.get('project_name', 'Unnamed Project')
        additional_context = request.form.get('additional_context', '')

        logger.debug(f"Project name: {project_name}")
        logger.debug(f"Simulation requirement: {simulation_requirement[:100]}...")

        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": "Please provide a simulation requirement description (simulation_requirement)"
            }), 400

        # Get uploaded files
        uploaded_files = request.files.getlist('files')
        if not uploaded_files or all(not f.filename for f in uploaded_files):
            return jsonify({
                "success": False,
                "error": "Please upload at least one document file"
            }), 400

        # Create project in DB
        project = repo.create(
            user_id=user_id,
            name=project_name,
            simulation_requirement=simulation_requirement,
        )
        logger.info(f"Created project: {project.id}")

        # Save files and extract text
        document_texts = []
        all_text = ""

        for file in uploaded_files:
            if file and file.filename and allowed_file(file.filename):
                # Save file to project directory + DB metadata
                file_info = repo.save_file_to_project(
                    project,
                    file,
                    file.filename
                )

                # Extract text
                text = FileParser.extract_text(file_info["storage_path"])
                text = TextProcessor.preprocess_text(text)
                document_texts.append(text)
                all_text += f"\n\n=== {file_info['filename']} ===\n{text}"

        if not document_texts:
            repo.delete(str(project.id), user_id)
            return jsonify({
                "success": False,
                "error": "No documents were successfully processed. Please check file formats."
            }), 400

        # Save extracted text to DB column
        repo.update(project, extracted_text=all_text)
        logger.info(f"Text extraction complete, {len(all_text)} characters total")

        # Generate ontology
        logger.info("Calling LLM to generate ontology definition...")
        generator = OntologyGenerator()
        ontology = generator.generate(
            document_texts=document_texts,
            simulation_requirement=simulation_requirement,
            additional_context=additional_context if additional_context else None
        )

        # Save ontology to project
        entity_count = len(ontology.get("entity_types", []))
        edge_count = len(ontology.get("edge_types", []))
        logger.info(f"Ontology generation complete: {entity_count} entity types, {edge_count} relationship types")

        ontology_data = {
            "entity_types": ontology.get("entity_types", []),
            "edge_types": ontology.get("edge_types", [])
        }
        analysis_summary = ontology.get("analysis_summary", "")

        repo.update(
            project,
            ontology=ontology_data,
            analysis_summary=analysis_summary,
            status="ontology_generated",
        )
        logger.info(f"=== Ontology generation complete === Project ID: {project.id}")

        return jsonify({
            "success": True,
            "data": {
                "project_id": str(project.id),
                "project_name": project.name,
                "ontology": project.ontology,
                "analysis_summary": project.analysis_summary,
                "files": project.seed_files,
                "total_text_length": len(all_text)
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== API 2: Build Graph ==============

@graph_bp.route('/build', methods=['POST'])
@require_auth
def build_graph():
    """
    API 2: Build graph based on project_id

    Request (JSON):
        {
            "project_id": "...",       // Required, from API 1
            "graph_name": "Graph Name", // Optional
            "chunk_size": 500,          // Optional, default 500
            "chunk_overlap": 50         // Optional, default 50
        }

    Returns:
        {
            "success": true,
            "data": {
                "project_id": "...",
                "task_id": "task_xxxx",
                "message": "Graph building task started"
            }
        }
    """
    try:
        logger.info("=== Starting graph building ===")

        session = g.db_session
        repo = ProjectRepository(session)
        user_id = g.current_user.id

        # Check configuration
        errors = []
        if not Config.ZEP_API_KEY:
            errors.append("ZEP_API_KEY is not configured")
        if errors:
            logger.error(f"Configuration errors: {errors}")
            return jsonify({
                "success": False,
                "error": "Configuration errors: " + "; ".join(errors)
            }), 500

        # Parse request
        data = request.get_json() or {}
        project_id = data.get('project_id')
        logger.debug(f"Request parameters: project_id={project_id}")

        if not project_id:
            return jsonify({
                "success": False,
                "error": "Please provide project_id"
            }), 400

        # Get project
        project = repo.get_by_id(project_id, user_id=user_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"Project not found: {project_id}"
            }), 404

        # Check project status
        force = data.get('force', False)  # Force rebuild
        step_data = dict(project.step_data or {})

        if project.status == "created":
            return jsonify({
                "success": False,
                "error": "Project ontology has not been generated yet. Please call /ontology/generate first."
            }), 400

        if project.status == "graph_building" and not force:
            return jsonify({
                "success": False,
                "error": "Graph is currently being built. Please do not submit again. To force rebuild, add force: true",
                "task_id": step_data.get("graph_build_task_id")
            }), 400

        # If force rebuild, reset status
        if force and project.status in ["graph_building", "failed", "graph_completed"]:
            repo.update(
                project,
                status="ontology_generated",
                graph_id=None,
            )
            step_data.pop("graph_build_task_id", None)
            step_data.pop("error", None)

        # Get configuration
        graph_name = data.get('graph_name', project.name or 'MiroFish Graph')
        chunk_size = data.get('chunk_size', project.chunk_size or Config.DEFAULT_CHUNK_SIZE)
        chunk_overlap = data.get('chunk_overlap', project.chunk_overlap or Config.DEFAULT_CHUNK_OVERLAP)

        # Update project configuration
        repo.update(project, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        # Get extracted text
        text = project.extracted_text
        if not text:
            return jsonify({
                "success": False,
                "error": "Extracted text content not found"
            }), 400

        # Get ontology
        ontology = project.ontology
        if not ontology:
            return jsonify({
                "success": False,
                "error": "Ontology definition not found"
            }), 400

        # Create async task
        task_manager = TaskManager()
        task_id = task_manager.create_task(f"Build graph: {graph_name}")
        logger.info(f"Created graph building task: task_id={task_id}, project_id={project_id}")

        # Update project status
        step_data["graph_build_task_id"] = task_id
        repo.update(
            project,
            status="graph_building",
            step_data=step_data,
        )

        # Capture project_id as string for the background thread
        project_id_str = str(project.id)

        # Start background task
        def build_task():
            build_logger = get_logger('mirofish.build')
            try:
                build_logger.info(f"[{task_id}] Starting graph building...")
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    message="Initializing graph building service..."
                )

                # Create graph building service
                builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)

                # Chunk text
                task_manager.update_task(
                    task_id,
                    message="Chunking text...",
                    progress=5
                )
                chunks = TextProcessor.split_text(
                    text,
                    chunk_size=chunk_size,
                    overlap=chunk_overlap
                )
                total_chunks = len(chunks)

                # Create graph
                task_manager.update_task(
                    task_id,
                    message="Creating Zep graph...",
                    progress=10
                )
                graph_id = builder.create_graph(name=graph_name)

                # Update project graph_id in a new session (background thread)
                with get_db() as bg_session:
                    bg_repo = ProjectRepository(bg_session)
                    bg_project = bg_repo.get_by_id(project_id_str)
                    if bg_project:
                        bg_repo.update(bg_project, graph_id=graph_id)

                # Set ontology
                task_manager.update_task(
                    task_id,
                    message="Setting ontology definition...",
                    progress=15
                )
                builder.set_ontology(graph_id, ontology)

                # Add text (progress_callback signature is (msg, progress_ratio))
                def add_progress_callback(msg, progress_ratio):
                    progress = 15 + int(progress_ratio * 40)  # 15% - 55%
                    task_manager.update_task(
                        task_id,
                        message=msg,
                        progress=progress
                    )

                task_manager.update_task(
                    task_id,
                    message=f"Adding {total_chunks} text chunks...",
                    progress=15
                )

                episode_uuids = builder.add_text_batches(
                    graph_id,
                    chunks,
                    batch_size=3,
                    progress_callback=add_progress_callback
                )

                # Wait for Zep processing to complete (query processed status for each episode)
                task_manager.update_task(
                    task_id,
                    message="Waiting for Zep to process data...",
                    progress=55
                )

                def wait_progress_callback(msg, progress_ratio):
                    progress = 55 + int(progress_ratio * 35)  # 55% - 90%
                    task_manager.update_task(
                        task_id,
                        message=msg,
                        progress=progress
                    )

                builder._wait_for_episodes(episode_uuids, wait_progress_callback)

                # Get graph data
                task_manager.update_task(
                    task_id,
                    message="Retrieving graph data...",
                    progress=95
                )
                graph_data = builder.get_graph_data(graph_id)

                # Update project status
                with get_db() as bg_session:
                    bg_repo = ProjectRepository(bg_session)
                    bg_project = bg_repo.get_by_id(project_id_str)
                    if bg_project:
                        bg_repo.update(bg_project, status="graph_completed")

                node_count = graph_data.get("node_count", 0)
                edge_count = graph_data.get("edge_count", 0)
                build_logger.info(f"[{task_id}] Graph building complete: graph_id={graph_id}, nodes={node_count}, edges={edge_count}")

                # Complete
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    message="Graph building complete",
                    progress=100,
                    result={
                        "project_id": project_id_str,
                        "graph_id": graph_id,
                        "node_count": node_count,
                        "edge_count": edge_count,
                        "chunk_count": total_chunks
                    }
                )

            except Exception as e:
                # Update project status to failed
                build_logger.error(f"[{task_id}] Graph building failed: {str(e)}")
                build_logger.debug(traceback.format_exc())

                with get_db() as bg_session:
                    bg_repo = ProjectRepository(bg_session)
                    bg_project = bg_repo.get_by_id(project_id_str)
                    if bg_project:
                        sd = dict(bg_project.step_data or {})
                        sd["error"] = str(e)
                        bg_repo.update(bg_project, status="failed", step_data=sd)

                task_manager.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    message=f"Build failed: {str(e)}",
                    error=traceback.format_exc()
                )

        # Start background thread
        thread = threading.Thread(target=build_task, daemon=True)
        thread.start()

        return jsonify({
            "success": True,
            "data": {
                "project_id": project_id_str,
                "task_id": task_id,
                "message": "Graph building task started. Check progress via /task/{task_id}"
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Task Query APIs ==============

@graph_bp.route('/task/<task_id>', methods=['GET'])
@require_auth
def get_task(task_id: str):
    """
    Query task status
    """
    task = TaskManager().get_task(task_id)

    if not task:
        return jsonify({
            "success": False,
            "error": f"Task not found: {task_id}"
        }), 404

    return jsonify({
        "success": True,
        "data": task.to_dict()
    })


@graph_bp.route('/tasks', methods=['GET'])
@require_auth
def list_tasks():
    """
    List all tasks
    """
    tasks = TaskManager().list_tasks()

    return jsonify({
        "success": True,
        "data": [t.to_dict() for t in tasks],
        "count": len(tasks)
    })


# ============== Graph Data APIs ==============

@graph_bp.route('/data/<graph_id>', methods=['GET'])
@require_auth
def get_graph_data(graph_id: str):
    """
    Get graph data (nodes and edges)
    """
    try:
        if not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": "ZEP_API_KEY is not configured"
            }), 500

        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
        graph_data = builder.get_graph_data(graph_id)

        return jsonify({
            "success": True,
            "data": graph_data
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@graph_bp.route('/delete/<graph_id>', methods=['DELETE'])
@require_auth
def delete_graph(graph_id: str):
    """
    Delete a Zep graph
    """
    try:
        if not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": "ZEP_API_KEY is not configured"
            }), 500

        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
        builder.delete_graph(graph_id)

        return jsonify({
            "success": True,
            "message": f"Graph deleted: {graph_id}"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500
