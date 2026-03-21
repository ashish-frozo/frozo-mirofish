"""
Report API routes
Provides simulation report generation, retrieval, conversation, and other endpoints
"""

import os
import traceback
import threading
from flask import request, jsonify, send_file, g

from . import report_bp
from ..config import Config
from ..services.report_agent import ReportAgent, ReportManager, ReportStatus
from ..services.simulation_manager import SimulationManager
from ..models.project import ProjectManager
from ..repositories.task_repo import TaskRepository
from ..repositories.report_repo import ReportRepository
from ..repositories.simulation_repo import SimulationRepository
from ..db import get_db
from ..utils.logger import get_logger
from ..middleware.auth import require_auth

logger = get_logger('mirofish.api.report')


# ============== Report Generation APIs ==============

@report_bp.route('/generate', methods=['POST'])
@require_auth
def generate_report():
    """
    Generate simulation analysis report (async task)

    This is a long-running operation. The API returns task_id immediately.
    Use GET /api/report/generate/status to check progress.

    Request (JSON):
        {
            "simulation_id": "sim_xxxx",    // Required, Simulation ID
            "force_regenerate": false        // Optional, force regeneration
        }

    Returns:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "task_id": "task_xxxx",
                "status": "generating",
                "message": "Report generation task started"
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "Please provide simulation_id"
            }), 400

        force_regenerate = data.get('force_regenerate', False)

        # Get simulation info — try DB first, then fall back to file-based manager
        graph_id = None
        project_id = None
        simulation_requirement = None
        sim_state = None

        with get_db() as session:
            sim_repo = SimulationRepository(session)
            db_sim = sim_repo.get_by_simulation_id(simulation_id)
            if db_sim:
                from ..repositories.project_repo import ProjectRepository
                proj_repo = ProjectRepository(session)
                db_project = proj_repo.get_by_id(db_sim.project_id)
                graph_id = db_project.graph_id if db_project else ''
                simulation_requirement = db_project.simulation_requirement if db_project else ''
                project_id = str(db_sim.project_id)
                sim_state = db_sim

        if not sim_state:
            # Fallback to file-based manager for legacy simulations
            manager = SimulationManager()
            state = manager.get_simulation(simulation_id)
            if not state:
                return jsonify({
                    "success": False,
                    "error": f"Simulation not found: {simulation_id}"
                }), 404
            project_id = state.project_id
            graph_id = state.graph_id
            simulation_requirement = None

            # Get project info for legacy path
            project = ProjectManager.get_project(project_id)
            if not project:
                return jsonify({
                    "success": False,
                    "error": f"Project not found: {project_id}"
                }), 404
            graph_id = state.graph_id or project.graph_id
            simulation_requirement = project.simulation_requirement

        # Check if report already exists
        if not force_regenerate:
            existing_report = ReportManager.get_report_by_simulation(simulation_id)
            if existing_report and existing_report.status == ReportStatus.COMPLETED:
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "report_id": existing_report.report_id,
                        "status": "completed",
                        "message": "Report already exists",
                        "already_generated": True
                    }
                })

        if not graph_id:
            return jsonify({
                "success": False,
                "error": "Missing graph ID. Please ensure the graph has been built."
            }), 400

        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": "Missing simulation requirement description"
            }), 400

        # Pre-generate report_id for immediate return to frontend
        import uuid
        report_id = f"report_{uuid.uuid4().hex[:12]}"

        # Create async task and DB report record
        db_report_id = None
        with get_db() as session:
            task_repo = TaskRepository(session)
            task = task_repo.create(
                user_id=g.current_user.id,
                task_type="report_generate",
                metadata={
                    "simulation_id": simulation_id,
                    "graph_id": graph_id,
                    "report_id": report_id,
                },
            )
            task_id = str(task.id)

            # Dual-write: create report record in DB
            try:
                report_repo = ReportRepository(session)
                sim_repo = SimulationRepository(session)
                sim_row = sim_repo.get_by_simulation_id(simulation_id)
                db_report = report_repo.create(
                    project_id=sim_row.project_id if sim_row else project_id,
                    simulation_id=sim_row.id if sim_row else None,
                    graph_id=graph_id,
                    simulation_requirement=simulation_requirement,
                )
                db_report_id = str(db_report.id)
            except Exception as exc:
                logger.warning(f"Failed to create DB report record (non-fatal): {exc}")

        # Define background task
        def run_generate():
            try:
                with get_db() as s:
                    TaskRepository(s).update_progress(
                        task_id, status="running", progress=0,
                        message="Initializing Report Agent..."
                    )
                    # Update DB report status
                    if db_report_id:
                        try:
                            ReportRepository(s).update(db_report_id, status="generating")
                        except Exception:
                            pass

                # Create Report Agent
                agent = ReportAgent(
                    graph_id=graph_id,
                    simulation_id=simulation_id,
                    simulation_requirement=simulation_requirement
                )

                # Progress callback
                def progress_callback(stage, progress, message):
                    with get_db() as s:
                        TaskRepository(s).update_progress(
                            task_id, progress=progress,
                            message=f"[{stage}] {message}"
                        )

                # Generate report (pass pre-generated report_id)
                report = agent.generate_report(
                    progress_callback=progress_callback,
                    report_id=report_id
                )

                # Save report (file-based)
                ReportManager.save_report(report)

                # Sync result back to DB
                if db_report_id:
                    try:
                        with get_db() as s:
                            repo = ReportRepository(s)
                            update_fields = {
                                "title": getattr(report, 'title', '') or report_id,
                                "summary": getattr(report, 'summary', None),
                                "markdown_content": getattr(report, 'markdown_content', None),
                                "status": report.status.value if hasattr(report.status, 'value') else str(report.status),
                                "error": getattr(report, 'error', None),
                            }
                            if hasattr(report, 'outline') and report.outline:
                                update_fields["outline"] = report.outline if isinstance(report.outline, dict) else {"sections": report.outline}
                            if report.status == ReportStatus.COMPLETED:
                                from datetime import datetime, timezone
                                update_fields["completed_at"] = datetime.now(timezone.utc)
                            repo.update(db_report_id, **update_fields)
                    except Exception as exc:
                        logger.warning(f"Failed to sync report to DB (non-fatal): {exc}")

                if report.status == ReportStatus.COMPLETED:
                    with get_db() as s:
                        TaskRepository(s).complete(task_id, result={
                            "report_id": report.report_id,
                            "simulation_id": simulation_id,
                            "status": "completed"
                        })
                else:
                    with get_db() as s:
                        TaskRepository(s).fail(task_id, error=report.error or "Report generation failed")

            except Exception as e:
                logger.error(f"Report generation failed: {str(e)}")
                with get_db() as s:
                    TaskRepository(s).fail(task_id, error=str(e))
                    # Mark DB report as failed
                    if db_report_id:
                        try:
                            ReportRepository(s).update(db_report_id, status="failed", error=str(e))
                        except Exception:
                            pass

        # Start background thread
        thread = threading.Thread(target=run_generate, daemon=True)
        thread.start()

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "report_id": report_id,
                "task_id": task_id,
                "status": "generating",
                "message": "Report generation task started. Check progress via /api/report/generate/status",
                "already_generated": False
            }
        })

    except Exception as e:
        logger.error(f"Failed to start report generation task: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/generate/status', methods=['POST'])
@require_auth
def get_generate_status():
    """
    Query report generation task progress

    Request (JSON):
        {
            "task_id": "task_xxxx",         // Optional, task_id from generate
            "simulation_id": "sim_xxxx"     // Optional, Simulation ID
        }

    Returns:
        {
            "success": true,
            "data": {
                "task_id": "task_xxxx",
                "status": "processing|completed|failed",
                "progress": 45,
                "message": "..."
            }
        }
    """
    try:
        data = request.get_json() or {}

        task_id = data.get('task_id')
        simulation_id = data.get('simulation_id')

        # If simulation_id provided, first check if a completed report exists
        if simulation_id:
            existing_report = ReportManager.get_report_by_simulation(simulation_id)
            if existing_report and existing_report.status == ReportStatus.COMPLETED:
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "report_id": existing_report.report_id,
                        "status": "completed",
                        "progress": 100,
                        "message": "Report has been generated",
                        "already_completed": True
                    }
                })

        if not task_id:
            return jsonify({
                "success": False,
                "error": "Please provide task_id or simulation_id"
            }), 400

        with get_db() as session:
            task_repo = TaskRepository(session)
            task = task_repo.get_by_id(task_id)

            if not task:
                return jsonify({
                    "success": False,
                    "error": f"Task not found: {task_id}"
                }), 404

            task_dict = {
                "task_id": str(task.id),
                "task_type": task.type,
                "status": task.status,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": None,
                "progress": task.progress,
                "message": task.message or "",
                "progress_detail": task.metadata_.get("progress_detail", {}) if task.metadata_ else {},
                "result": task.result,
                "error": task.error,
                "metadata": task.metadata_ or {},
            }

        return jsonify({
            "success": True,
            "data": task_dict
        })

    except Exception as e:
        logger.error(f"Failed to query task status: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Report Retrieval APIs ==============

@report_bp.route('/<report_id>', methods=['GET'])
@require_auth
def get_report(report_id: str):
    """
    Get report details

    Returns:
        {
            "success": true,
            "data": {
                "report_id": "report_xxxx",
                "simulation_id": "sim_xxxx",
                "status": "completed",
                "outline": {...},
                "markdown_content": "...",
                "created_at": "...",
                "completed_at": "..."
            }
        }
    """
    try:
        # Try file-based first (primary source during migration)
        report = ReportManager.get_report(report_id)

        if not report:
            return jsonify({
                "success": False,
                "error": f"Report not found: {report_id}"
            }), 404

        return jsonify({
            "success": True,
            "data": report.to_dict()
        })

    except Exception as e:
        logger.error(f"Failed to get report: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/by-simulation/<simulation_id>', methods=['GET'])
@require_auth
def get_report_by_simulation(simulation_id: str):
    """
    Get report by simulation ID

    Returns:
        {
            "success": true,
            "data": {
                "report_id": "report_xxxx",
                ...
            }
        }
    """
    try:
        report = ReportManager.get_report_by_simulation(simulation_id)

        if not report:
            return jsonify({
                "success": False,
                "error": f"No report available for this simulation: {simulation_id}",
                "has_report": False
            }), 404

        return jsonify({
            "success": True,
            "data": report.to_dict(),
            "has_report": True
        })

    except Exception as e:
        logger.error(f"Failed to get report: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/list', methods=['GET'])
@require_auth
def list_reports():
    """
    List all reports

    Query parameters:
        simulation_id: Filter by simulation ID (optional)
        limit: Return count limit (default 50)

    Returns:
        {
            "success": true,
            "data": [...],
            "count": 10
        }
    """
    try:
        simulation_id = request.args.get('simulation_id')
        limit = request.args.get('limit', 50, type=int)

        reports = ReportManager.list_reports(
            simulation_id=simulation_id,
            limit=limit
        )

        return jsonify({
            "success": True,
            "data": [r.to_dict() for r in reports],
            "count": len(reports)
        })

    except Exception as e:
        logger.error(f"Failed to list reports: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/<report_id>/download', methods=['GET'])
@require_auth
def download_report(report_id: str):
    """
    Download report in Markdown or HTML format.

    Query params:
        format: 'md' (default) or 'html'

    Returns a downloadable file attachment.
    """
    try:
        fmt = request.args.get('format', 'md')  # 'md' or 'html'

        # Get report content — try DB first, then file-based fallback
        markdown_content = None
        report_title = "Prediction Report"

        with get_db() as session:
            report_repo = ReportRepository(session)
            db_report = report_repo.get_by_id(report_id)
            if db_report and db_report.markdown_content:
                markdown_content = db_report.markdown_content
                report_title = db_report.title or report_title

        if not markdown_content:
            # Fallback to file-based manager
            report = ReportManager.get_report(report_id)
            if report and report.markdown_content:
                markdown_content = report.markdown_content
                report_title = getattr(report, 'title', report_title) or report_title

        if not markdown_content:
            return jsonify({
                "success": False,
                "error": "Report not found or has no content"
            }), 404

        # Sanitize title for use as filename
        safe_title = "".join(c for c in report_title if c.isalnum() or c in ' -_')[:50].strip()
        base_name = safe_title or report_id

        import tempfile

        if fmt == 'html':
            import markdown as md_lib
            html_body = md_lib.markdown(markdown_content, extensions=['tables', 'fenced_code'])
            html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{report_title}</title>
    <style>
        body {{ font-family: 'Inter', -apple-system, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; color: #1e293b; line-height: 1.7; }}
        h1 {{ color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; }}
        h2 {{ color: #1e293b; margin-top: 32px; }}
        blockquote {{ border-left: 4px solid #4f46e5; margin: 16px 0; padding: 12px 20px; background: #f8fafc; color: #475569; }}
        code {{ background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
        pre {{ background: #1e293b; color: #e2e8f0; padding: 16px; border-radius: 8px; overflow-x: auto; }}
        table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
        th, td {{ border: 1px solid #e2e8f0; padding: 8px 12px; text-align: left; }}
        th {{ background: #f8fafc; font-weight: 600; }}
        hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 24px 0; }}
        ul, ol {{ padding-left: 24px; }}
        li {{ margin: 4px 0; }}
        strong {{ color: #0f172a; }}
        @media print {{ body {{ max-width: 100%; margin: 20px; }} }}
    </style>
</head>
<body>
{html_body}
<footer style="margin-top: 48px; padding-top: 16px; border-top: 1px solid #e2e8f0; color: #94a3b8; font-size: 0.85em;">
    Generated by Augur AI Prediction Engine
</footer>
</body>
</html>"""

            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_doc)
                temp_path = f.name

            return send_file(temp_path, as_attachment=True, download_name=f"{base_name}.html")

        else:  # markdown
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
                f.write(markdown_content)
                temp_path = f.name

            return send_file(temp_path, as_attachment=True, download_name=f"{base_name}.md")

    except Exception as e:
        logger.error(f"Failed to download report: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/<report_id>', methods=['DELETE'])
@require_auth
def delete_report(report_id: str):
    """Delete a report"""
    try:
        success = ReportManager.delete_report(report_id)

        # Dual-write: also delete from DB (best-effort)
        try:
            with get_db() as session:
                ReportRepository(session).delete(report_id)
        except Exception as exc:
            logger.debug(f"DB report delete skipped (non-fatal): {exc}")

        if not success:
            return jsonify({
                "success": False,
                "error": f"Report not found: {report_id}"
            }), 404

        return jsonify({
            "success": True,
            "message": f"Report deleted: {report_id}"
        })

    except Exception as e:
        logger.error(f"Failed to delete report: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Report Agent Conversation API ==============

@report_bp.route('/chat', methods=['POST'])
@require_auth
def chat_with_report_agent():
    """
    Chat with Report Agent

    Report Agent can autonomously call retrieval tools during conversation to answer questions

    Request (JSON):
        {
            "simulation_id": "sim_xxxx",        // Required, Simulation ID
            "message": "Please explain the public opinion trend",    // Required, user message
            "chat_history": [                   // Optional, conversation history
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ]
        }

    Returns:
        {
            "success": true,
            "data": {
                "response": "Agent reply...",
                "tool_calls": [list of tools called],
                "sources": [information sources]
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        message = data.get('message')
        chat_history = data.get('chat_history', [])

        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "Please provide simulation_id"
            }), 400

        if not message:
            return jsonify({
                "success": False,
                "error": "Please provide message"
            }), 400

        # Get simulation and project info — try DB first, then fall back to file-based manager
        graph_id = None
        simulation_requirement = ""
        sim_state = None

        with get_db() as session:
            sim_repo = SimulationRepository(session)
            db_sim = sim_repo.get_by_simulation_id(simulation_id)
            if db_sim:
                from ..repositories.project_repo import ProjectRepository
                proj_repo = ProjectRepository(session)
                db_project = proj_repo.get_by_id(db_sim.project_id)
                graph_id = db_project.graph_id if db_project else ''
                simulation_requirement = (db_project.simulation_requirement or '') if db_project else ''
                sim_state = db_sim

        if not sim_state:
            # Fallback to file-based manager for legacy simulations
            manager = SimulationManager()
            state = manager.get_simulation(simulation_id)
            if not state:
                return jsonify({
                    "success": False,
                    "error": f"Simulation not found: {simulation_id}"
                }), 404

            project = ProjectManager.get_project(state.project_id)
            if not project:
                return jsonify({
                    "success": False,
                    "error": f"Project not found: {state.project_id}"
                }), 404
            graph_id = state.graph_id or project.graph_id
            simulation_requirement = project.simulation_requirement or ""

        if not graph_id:
            return jsonify({
                "success": False,
                "error": "Missing graph ID"
            }), 400

        # Create Agent and conduct conversation
        agent = ReportAgent(
            graph_id=graph_id,
            simulation_id=simulation_id,
            simulation_requirement=simulation_requirement
        )

        result = agent.chat(message=message, chat_history=chat_history)

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        logger.error(f"Conversation failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Report Progress and Section APIs ==============

@report_bp.route('/<report_id>/progress', methods=['GET'])
@require_auth
def get_report_progress(report_id: str):
    """
    Get report generation progress (realtime)

    Returns:
        {
            "success": true,
            "data": {
                "status": "generating",
                "progress": 45,
                "message": "Generating section: Key Findings",
                "current_section": "Key Findings",
                "completed_sections": ["Executive Summary", "Simulation Background"],
                "updated_at": "2025-12-09T..."
            }
        }
    """
    try:
        progress = ReportManager.get_progress(report_id)

        if not progress:
            return jsonify({
                "success": False,
                "error": f"Report not found or progress info unavailable: {report_id}"
            }), 404

        return jsonify({
            "success": True,
            "data": progress
        })

    except Exception as e:
        logger.error(f"Failed to get report progress: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/<report_id>/sections', methods=['GET'])
@require_auth
def get_report_sections(report_id: str):
    """
    Get list of generated sections (section-by-section output)

    Frontend can poll this endpoint to get generated section content without waiting for the entire report to complete

    Returns:
        {
            "success": true,
            "data": {
                "report_id": "report_xxxx",
                "sections": [
                    {
                        "filename": "section_01.md",
                        "section_index": 1,
                        "content": "## Executive Summary\\n\\n..."
                    },
                    ...
                ],
                "total_sections": 3,
                "is_complete": false
            }
        }
    """
    try:
        sections = ReportManager.get_generated_sections(report_id)

        # Get report status
        report = ReportManager.get_report(report_id)
        is_complete = report is not None and report.status == ReportStatus.COMPLETED

        return jsonify({
            "success": True,
            "data": {
                "report_id": report_id,
                "sections": sections,
                "total_sections": len(sections),
                "is_complete": is_complete
            }
        })

    except Exception as e:
        logger.error(f"Failed to get section list: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/<report_id>/section/<int:section_index>', methods=['GET'])
@require_auth
def get_single_section(report_id: str, section_index: int):
    """
    Get single section content

    Returns:
        {
            "success": true,
            "data": {
                "filename": "section_01.md",
                "content": "## Executive Summary\\n\\n..."
            }
        }
    """
    try:
        section_path = ReportManager._get_section_path(report_id, section_index)

        if not os.path.exists(section_path):
            return jsonify({
                "success": False,
                "error": f"Section not found: section_{section_index:02d}.md"
            }), 404

        with open(section_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return jsonify({
            "success": True,
            "data": {
                "filename": f"section_{section_index:02d}.md",
                "section_index": section_index,
                "content": content
            }
        })

    except Exception as e:
        logger.error(f"Failed to get section content: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Report Status Check API ==============

@report_bp.route('/check/<simulation_id>', methods=['GET'])
@require_auth
def check_report_status(simulation_id: str):
    """
    Check if a simulation has a report and its status

    Used by frontend to determine if the Interview feature should be unlocked

    Returns:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "has_report": true,
                "report_status": "completed",
                "report_id": "report_xxxx",
                "interview_unlocked": true
            }
        }
    """
    try:
        report = ReportManager.get_report_by_simulation(simulation_id)

        has_report = report is not None
        report_status = report.status.value if report else None
        report_id = report.report_id if report else None

        # Only unlock interview after report is completed
        interview_unlocked = has_report and report.status == ReportStatus.COMPLETED

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "has_report": has_report,
                "report_status": report_status,
                "report_id": report_id,
                "interview_unlocked": interview_unlocked
            }
        })

    except Exception as e:
        logger.error(f"Failed to check report status: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Agent Log APIs ==============

@report_bp.route('/<report_id>/agent-log', methods=['GET'])
@require_auth
def get_agent_log(report_id: str):
    """
    Get Report Agent detailed execution log

    Realtime retrieval of every action during report generation, including:
    - Report start, planning start/complete
    - Each section's start, tool calls, LLM responses, completion
    - Report complete or failed

    Query parameters:
        from_line: Starting line number (optional, default 0, for incremental retrieval)

    Returns:
        {
            "success": true,
            "data": {
                "logs": [
                    {
                        "timestamp": "2025-12-13T...",
                        "elapsed_seconds": 12.5,
                        "report_id": "report_xxxx",
                        "action": "tool_call",
                        "stage": "generating",
                        "section_title": "Executive Summary",
                        "section_index": 1,
                        "details": {
                            "tool_name": "insight_forge",
                            "parameters": {...},
                            ...
                        }
                    },
                    ...
                ],
                "total_lines": 25,
                "from_line": 0,
                "has_more": false
            }
        }
    """
    try:
        from_line = request.args.get('from_line', 0, type=int)

        log_data = ReportManager.get_agent_log(report_id, from_line=from_line)

        return jsonify({
            "success": True,
            "data": log_data
        })

    except Exception as e:
        logger.error(f"Failed to get Agent log: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/<report_id>/agent-log/stream', methods=['GET'])
@require_auth
def stream_agent_log(report_id: str):
    """
    Get complete Agent log (one-time full retrieval)

    Returns:
        {
            "success": true,
            "data": {
                "logs": [...],
                "count": 25
            }
        }
    """
    try:
        logs = ReportManager.get_agent_log_stream(report_id)

        return jsonify({
            "success": True,
            "data": {
                "logs": logs,
                "count": len(logs)
            }
        })

    except Exception as e:
        logger.error(f"Failed to get Agent log: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Console Log APIs ==============

@report_bp.route('/<report_id>/console-log', methods=['GET'])
@require_auth
def get_console_log(report_id: str):
    """
    Get Report Agent console output log

    Realtime retrieval of console output (INFO, WARNING, etc.) during report generation.
    This differs from the agent-log endpoint which returns structured JSON logs;
    this returns plain-text console-style logs.

    Query parameters:
        from_line: Starting line number (optional, default 0, for incremental retrieval)

    Returns:
        {
            "success": true,
            "data": {
                "logs": [
                    "[19:46:14] INFO: Search complete: found 15 relevant facts",
                    "[19:46:14] INFO: Graph search: graph_id=xxx, query=...",
                    ...
                ],
                "total_lines": 100,
                "from_line": 0,
                "has_more": false
            }
        }
    """
    try:
        from_line = request.args.get('from_line', 0, type=int)

        log_data = ReportManager.get_console_log(report_id, from_line=from_line)

        return jsonify({
            "success": True,
            "data": log_data
        })

    except Exception as e:
        logger.error(f"Failed to get console log: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/<report_id>/console-log/stream', methods=['GET'])
@require_auth
def stream_console_log(report_id: str):
    """
    Get complete console log (one-time full retrieval)

    Returns:
        {
            "success": true,
            "data": {
                "logs": [...],
                "count": 100
            }
        }
    """
    try:
        logs = ReportManager.get_console_log_stream(report_id)

        return jsonify({
            "success": True,
            "data": {
                "logs": logs,
                "count": len(logs)
            }
        })

    except Exception as e:
        logger.error(f"Failed to get console log: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Tool Call APIs (for debugging) ==============

@report_bp.route('/tools/search', methods=['POST'])
@require_auth
def search_graph_tool():
    """
    Graph search tool endpoint (for debugging)

    Request (JSON):
        {
            "graph_id": "mirofish_xxxx",
            "query": "search query",
            "limit": 10
        }
    """
    try:
        data = request.get_json() or {}

        graph_id = data.get('graph_id')
        query = data.get('query')
        limit = data.get('limit', 10)

        if not graph_id or not query:
            return jsonify({
                "success": False,
                "error": "Please provide graph_id and query"
            }), 400

        from ..services.zep_tools import ZepToolsService

        tools = ZepToolsService()
        result = tools.search_graph(
            graph_id=graph_id,
            query=query,
            limit=limit
        )

        return jsonify({
            "success": True,
            "data": result.to_dict()
        })

    except Exception as e:
        logger.error(f"Graph search failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/tools/statistics', methods=['POST'])
@require_auth
def get_graph_statistics_tool():
    """
    Graph statistics tool endpoint (for debugging)

    Request (JSON):
        {
            "graph_id": "mirofish_xxxx"
        }
    """
    try:
        data = request.get_json() or {}

        graph_id = data.get('graph_id')

        if not graph_id:
            return jsonify({
                "success": False,
                "error": "Please provide graph_id"
            }), 400

        from ..services.zep_tools import ZepToolsService

        tools = ZepToolsService()
        result = tools.get_graph_statistics(graph_id)

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        logger.error(f"Failed to get graph statistics: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500
