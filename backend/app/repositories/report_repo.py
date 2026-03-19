"""Report repository — replaces file-based ReportManager."""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from ..models.db_models import ReportModel, ReportSectionModel, ReportLogModel


class ReportRepository:
    def __init__(self, session: Session):
        self.session = session

    # --- Report CRUD ---
    def create(self, project_id, simulation_id=None, graph_id=None, simulation_requirement=None) -> ReportModel:
        report = ReportModel(
            project_id=project_id,
            simulation_id=simulation_id,
            graph_id=graph_id,
            simulation_requirement=simulation_requirement,
            status="pending",
            title="",
        )
        self.session.add(report)
        self.session.flush()
        return report

    def get_by_id(self, report_id) -> ReportModel | None:
        return self.session.query(ReportModel).filter(ReportModel.id == report_id).first()

    def get_by_simulation(self, simulation_id) -> ReportModel | None:
        return self.session.query(ReportModel).filter(
            ReportModel.simulation_id == simulation_id
        ).order_by(ReportModel.created_at.desc()).first()

    def list_by_project(self, project_id, limit=20) -> list[ReportModel]:
        return self.session.query(ReportModel).filter(
            ReportModel.project_id == project_id
        ).order_by(ReportModel.created_at.desc()).limit(limit).all()

    def update(self, report_id, **kwargs) -> ReportModel | None:
        report = self.get_by_id(report_id)
        if not report:
            return None
        for key, value in kwargs.items():
            if hasattr(report, key):
                setattr(report, key, value)
        self.session.flush()
        return report

    def delete(self, report_id) -> bool:
        report = self.get_by_id(report_id)
        if not report:
            return False
        self.session.delete(report)
        self.session.flush()
        return True

    # --- Sections ---
    def save_section(self, report_id, section_index: int, title: str, content: str = None, tool_calls: list = None, status: str = "pending"):
        existing = self.session.query(ReportSectionModel).filter(
            ReportSectionModel.report_id == report_id,
            ReportSectionModel.section_index == section_index,
        ).first()
        if existing:
            if content is not None:
                existing.content = content
            if tool_calls is not None:
                existing.tool_calls = tool_calls
            if status:
                existing.status = status
        else:
            section = ReportSectionModel(
                report_id=report_id,
                section_index=section_index,
                title=title,
                content=content,
                tool_calls=tool_calls or [],
                status=status,
            )
            self.session.add(section)
        self.session.flush()

    def get_sections(self, report_id) -> list[ReportSectionModel]:
        return self.session.query(ReportSectionModel).filter(
            ReportSectionModel.report_id == report_id
        ).order_by(ReportSectionModel.section_index).all()

    # --- Logs ---
    def append_log(self, report_id, log_type: str, entry: dict):
        """Append a single log entry. Creates the log record if it doesn't exist."""
        log = self.session.query(ReportLogModel).filter(
            ReportLogModel.report_id == report_id,
            ReportLogModel.log_type == log_type,
        ).first()
        if log:
            entries = list(log.entries or [])
            entries.append(entry)
            log.entries = entries
        else:
            log = ReportLogModel(
                report_id=report_id,
                log_type=log_type,
                entries=[entry],
            )
            self.session.add(log)
        self.session.flush()

    def get_logs(self, report_id, log_type: str, from_line: int = 0) -> list[dict]:
        log = self.session.query(ReportLogModel).filter(
            ReportLogModel.report_id == report_id,
            ReportLogModel.log_type == log_type,
        ).first()
        if not log:
            return []
        entries = log.entries or []
        return entries[from_line:]
