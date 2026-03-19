"""Chat repository — persists conversation sessions and messages."""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from ..models.db_models import ChatSessionModel, ChatMessageModel


class ChatRepository:
    def __init__(self, session: Session):
        self.session = session

    # --- Sessions ---
    def create_session(self, project_id, agent_type: str, agent_index: int = None, agent_name: str = None) -> ChatSessionModel:
        chat_session = ChatSessionModel(
            project_id=project_id,
            agent_type=agent_type,
            agent_index=agent_index,
            agent_name=agent_name,
        )
        self.session.add(chat_session)
        self.session.flush()
        return chat_session

    def get_session(self, session_id) -> ChatSessionModel | None:
        return self.session.query(ChatSessionModel).filter(ChatSessionModel.id == session_id).first()

    def get_sessions_by_project(self, project_id) -> list[ChatSessionModel]:
        return self.session.query(ChatSessionModel).filter(
            ChatSessionModel.project_id == project_id
        ).order_by(ChatSessionModel.updated_at.desc()).all()

    def get_or_create_session(self, project_id, agent_type: str, agent_index: int = None, agent_name: str = None) -> ChatSessionModel:
        """Get existing session or create new one."""
        query = self.session.query(ChatSessionModel).filter(
            ChatSessionModel.project_id == project_id,
            ChatSessionModel.agent_type == agent_type,
        )
        if agent_index is not None:
            query = query.filter(ChatSessionModel.agent_index == agent_index)
        existing = query.first()
        if existing:
            return existing
        return self.create_session(project_id, agent_type, agent_index, agent_name)

    # --- Messages ---
    def add_message(self, session_id, role: str, content: str, tool_calls: dict = None) -> ChatMessageModel:
        message = ChatMessageModel(
            session_id=session_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
        )
        self.session.add(message)
        # Update session timestamp
        chat_session = self.get_session(session_id)
        if chat_session:
            chat_session.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return message

    def get_messages(self, session_id, limit: int = 100, offset: int = 0) -> list[ChatMessageModel]:
        return (
            self.session.query(ChatMessageModel)
            .filter(ChatMessageModel.session_id == session_id)
            .order_by(ChatMessageModel.created_at.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_message_count(self, session_id) -> int:
        return self.session.query(ChatMessageModel).filter(
            ChatMessageModel.session_id == session_id
        ).count()
