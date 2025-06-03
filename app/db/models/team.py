# app/db/models/team.py
from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from app.db.models.base_entity import BaseEntity


class Team(BaseEntity):
    """
    Team model for organizing users within organizations or tenants.
    Teams provide a way to group users for collaboration and access control.
    """

    __tablename__ = "teams"

    # Basic team information
    name = Column(String(255), nullable=False, comment="Team name")
    description = Column(Text, nullable=True, comment="Team description")

    # Relationships
    models = relationship("Model", back_populates="team")
    received_permissions = relationship("ModelPermission", foreign_keys="ModelPermission.team_id", back_populates="target_team")

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}', tenant_id={self.tenant_id})>"
