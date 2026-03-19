"""Tests for TaskRepository."""

import pytest
from app.repositories.task_repo import TaskRepository
from app.repositories.user_repo import UserRepository


class TestTaskRepository:
    @pytest.fixture
    def user(self, db_session):
        repo = UserRepository(db_session)
        return repo.create(email="taskuser@test.com", name="Task User", password="pass123")

    def test_create_task(self, db_session, user):
        repo = TaskRepository(db_session)
        task = repo.create(user_id=user.id, task_type="ontology_generation")
        assert task.status == "pending"
        assert task.type == "ontology_generation"
        assert task.user_id == user.id
        assert task.progress == 0

    def test_update_progress(self, db_session, user):
        repo = TaskRepository(db_session)
        task = repo.create(user_id=user.id, task_type="graph_build")
        repo.update_progress(task.id, status="running", progress=50, message="Building...")
        refreshed = repo.get_by_id(task.id)
        assert refreshed.status == "running"
        assert refreshed.progress == 50
        assert refreshed.message == "Building..."
        assert refreshed.started_at is not None

    def test_complete_task(self, db_session, user):
        repo = TaskRepository(db_session)
        task = repo.create(user_id=user.id, task_type="report_generation")
        repo.complete(task.id, result={"report_id": "abc123"})
        refreshed = repo.get_by_id(task.id)
        assert refreshed.status == "completed"
        assert refreshed.progress == 100
        assert refreshed.result == {"report_id": "abc123"}
        assert refreshed.completed_at is not None

    def test_fail_task(self, db_session, user):
        repo = TaskRepository(db_session)
        task = repo.create(user_id=user.id, task_type="simulation_run")
        repo.fail(task.id, error="Something broke")
        refreshed = repo.get_by_id(task.id)
        assert refreshed.status == "failed"
        assert refreshed.error == "Something broke"

    def test_find_by_status(self, db_session, user):
        repo = TaskRepository(db_session)
        repo.create(user_id=user.id, task_type="sim1")
        t2 = repo.create(user_id=user.id, task_type="sim2")
        repo.update_progress(t2.id, status="running")
        running = repo.find_by_status("running")
        assert len(running) == 1
        assert running[0].type == "sim2"

    def test_recover_stale(self, db_session, user):
        repo = TaskRepository(db_session)
        t1 = repo.create(user_id=user.id, task_type="stale1")
        t2 = repo.create(user_id=user.id, task_type="stale2")
        repo.update_progress(t1.id, status="running")
        repo.update_progress(t2.id, status="running")
        count = repo.recover_stale()
        assert count == 2
        assert repo.get_by_id(t1.id).status == "failed"
        assert "Server restarted" in repo.get_by_id(t1.id).error

    def test_get_nonexistent(self, db_session):
        import uuid
        repo = TaskRepository(db_session)
        assert repo.get_by_id(uuid.uuid4()) is None
