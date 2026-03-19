"""Task repository — replaces in-memory TaskManager."""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from ..models.db_models import TaskModel


class TaskRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, user_id, task_type: str, project_id=None, metadata: dict = None) -> TaskModel:
        task = TaskModel(
            user_id=user_id,
            project_id=project_id,
            type=task_type,
            status="pending",
            metadata_=metadata or {},
        )
        self.session.add(task)
        self.session.flush()
        return task

    def get_by_id(self, task_id) -> TaskModel | None:
        return self.session.query(TaskModel).filter(TaskModel.id == task_id).first()

    def update_progress(self, task_id, status: str = None, progress: int = None, message: str = None):
        task = self.get_by_id(task_id)
        if not task:
            return
        if status:
            task.status = status
            if status == "running" and not task.started_at:
                task.started_at = datetime.now(timezone.utc)
        if progress is not None:
            task.progress = progress
        if message:
            task.message = message
        self.session.flush()

    def complete(self, task_id, result: dict = None):
        task = self.get_by_id(task_id)
        if not task:
            return
        task.status = "completed"
        task.progress = 100
        task.result = result
        task.completed_at = datetime.now(timezone.utc)
        self.session.flush()

    def fail(self, task_id, error: str):
        task = self.get_by_id(task_id)
        if not task:
            return
        task.status = "failed"
        task.error = error
        task.completed_at = datetime.now(timezone.utc)
        self.session.flush()

    def find_by_status(self, status: str) -> list[TaskModel]:
        return self.session.query(TaskModel).filter(TaskModel.status == status).all()

    def recover_stale(self):
        """Mark all 'running' tasks as failed (called on server startup)."""
        stale = self.find_by_status("running")
        for task in stale:
            task.status = "failed"
            task.error = "Server restarted during execution. Please retry."
            task.completed_at = datetime.now(timezone.utc)
        self.session.flush()
        return len(stale)
