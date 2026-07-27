"""Team model"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Team(Base):
    """Team model"""
    __tablename__ = "teams"

    team_id = Column(Integer, primary_key=True)
    abbreviation = Column(String(10), nullable=False, unique=True)
    nickname = Column(String(100), nullable=False)
    full_name = Column(String(200), nullable=False, index=True)
    city = Column(String(100), nullable=True)
    year_founded = Column(Integer, nullable=True)
    arena = Column(String(200), nullable=True)
    conference = Column(String(20), nullable=True, comment="East/West")
    division = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    home_games = relationship("Game", foreign_keys="Game.home_team_id", back_populates="home_team")
    away_games = relationship("Game", foreign_keys="Game.away_team_id", back_populates="away_team")
    season_stats = relationship("TeamSeasonStats", back_populates="team", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Team(id={self.team_id}, name='{self.full_name}')>"
