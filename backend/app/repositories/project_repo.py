"""Project repository — replaces file-based ProjectManager."""

import os
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from ..models.db_models import ProjectModel
from ..config import Config
from ..services.cache_service import cache_invalidate_pattern


class ProjectRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, user_id, name: str, simulation_requirement: str = None, description: str = None) -> ProjectModel:
        project = ProjectModel(
            user_id=user_id,
            name=name,
            description=description,
            simulation_requirement=simulation_requirement,
            status="created",
            current_step=1,
        )
        self.session.add(project)
        self.session.flush()
        cache_invalidate_pattern(f"projects:{user_id}*")
        return project

    def get_by_id(self, project_id, user_id=None) -> ProjectModel | None:
        query = self.session.query(ProjectModel).filter(ProjectModel.id == project_id)
        if user_id:
            query = query.filter(ProjectModel.user_id == user_id)
        return query.first()

    def list_by_user(self, user_id, limit: int = 50, offset: int = 0) -> list[ProjectModel]:
        return (
            self.session.query(ProjectModel)
            .filter(ProjectModel.user_id == user_id)
            .order_by(ProjectModel.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def update(self, project: ProjectModel, **kwargs) -> ProjectModel:
        """Update project fields in-place. The project must already be attached to the session."""
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
        project.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        if project.user_id:
            cache_invalidate_pattern(f"projects:{project.user_id}*")
        return project

    def delete(self, project_id, user_id) -> bool:
        project = self.get_by_id(project_id, user_id)
        if not project:
            return False
        self.session.delete(project)
        self.session.flush()
        cache_invalidate_pattern(f"projects:{user_id}*")
        return True

    def save_file_to_project(self, project: ProjectModel, file, filename: str) -> dict:
        """Save uploaded file to disk, store metadata in DB seed_files JSONB."""
        # Create project files directory
        project_dir = os.path.join(Config.UPLOAD_FOLDER, 'projects', str(project.id), 'files')
        os.makedirs(project_dir, exist_ok=True)

        # Generate unique filename
        ext = os.path.splitext(filename)[1]
        storage_name = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(project_dir, storage_name)

        # Save file
        file.save(file_path)

        # Build file info
        file_info = {
            "filename": filename,
            "storage_name": storage_name,
            "storage_path": file_path,
            "size": os.path.getsize(file_path),
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }

        # Update seed_files metadata in DB
        seed_files = list(project.seed_files or [])
        seed_files.append(file_info)
        project.seed_files = seed_files
        self.session.flush()

        return file_info
