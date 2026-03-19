"""Simulation repository — replaces file-based SimulationManager state."""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from ..models.db_models import (
    SimulationModel, AgentProfileModel,
    SimulationActionModel, SimulationRoundSummaryModel
)


class SimulationRepository:
    def __init__(self, session: Session):
        self.session = session

    # --- Simulation CRUD ---
    def create(self, project_id, enable_twitter=True, enable_reddit=True, max_rounds=10) -> SimulationModel:
        sim = SimulationModel(
            project_id=project_id,
            enable_twitter=enable_twitter,
            enable_reddit=enable_reddit,
            max_rounds=max_rounds,
            status="pending",
        )
        self.session.add(sim)
        self.session.flush()
        return sim

    def get_by_id(self, sim_id) -> SimulationModel | None:
        return self.session.query(SimulationModel).filter(SimulationModel.id == sim_id).first()

    def get_by_project(self, project_id) -> list[SimulationModel]:
        return self.session.query(SimulationModel).filter(
            SimulationModel.project_id == project_id
        ).order_by(SimulationModel.created_at.desc()).all()

    def get_by_simulation_id(self, simulation_id: str) -> SimulationModel | None:
        """Look up by the legacy string simulation_id field (e.g. 'sim_xxxx')."""
        return self.session.query(SimulationModel).filter(
            SimulationModel.simulation_id == simulation_id
        ).first()

    def update(self, sim_id, **kwargs) -> SimulationModel | None:
        sim = self.get_by_id(sim_id)
        if not sim:
            return None
        for key, value in kwargs.items():
            if hasattr(sim, key):
                setattr(sim, key, value)
        self.session.flush()
        return sim

    # --- Agent Profiles ---
    def save_profiles(self, sim_id, profiles: list[dict]) -> list[AgentProfileModel]:
        models = []
        for p in profiles:
            model = AgentProfileModel(
                simulation_id=sim_id,
                agent_index=p.get("agent_index", 0),
                name=p.get("name", ""),
                role=p.get("role", ""),
                bio=p.get("bio", ""),
                personality=p.get("personality", {}),
                profile_data=p.get("profile_data", {}),
            )
            self.session.add(model)
            models.append(model)
        self.session.flush()
        return models

    def get_profiles(self, sim_id) -> list[AgentProfileModel]:
        return self.session.query(AgentProfileModel).filter(
            AgentProfileModel.simulation_id == sim_id
        ).order_by(AgentProfileModel.agent_index).all()

    # --- Actions ---
    def save_action(self, sim_id, round_num, agent_index, agent_name, platform, action_type, content=None, target_id=None, metadata=None):
        action = SimulationActionModel(
            simulation_id=sim_id,
            round=round_num,
            agent_index=agent_index,
            agent_name=agent_name,
            platform=platform,
            action_type=action_type,
            content=content,
            target_id=target_id,
            metadata_=metadata or {},
        )
        self.session.add(action)
        self.session.flush()
        return action

    def get_actions(self, sim_id, round_num=None, platform=None, limit=100) -> list[SimulationActionModel]:
        query = self.session.query(SimulationActionModel).filter(
            SimulationActionModel.simulation_id == sim_id
        )
        if round_num is not None:
            query = query.filter(SimulationActionModel.round == round_num)
        if platform:
            query = query.filter(SimulationActionModel.platform == platform)
        return query.order_by(SimulationActionModel.created_at.desc()).limit(limit).all()

    # --- Round Summaries ---
    def save_round_summary(self, sim_id, round_num, platform, summary: dict):
        existing = self.session.query(SimulationRoundSummaryModel).filter(
            SimulationRoundSummaryModel.simulation_id == sim_id,
            SimulationRoundSummaryModel.round == round_num,
            SimulationRoundSummaryModel.platform == platform,
        ).first()
        if existing:
            existing.summary = summary
        else:
            model = SimulationRoundSummaryModel(
                simulation_id=sim_id,
                round=round_num,
                platform=platform,
                summary=summary,
            )
            self.session.add(model)
        self.session.flush()
