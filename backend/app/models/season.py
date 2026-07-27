"""Season model"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Season(Base):
    """Season model"""
    __tablename__ = "seasons"

    season_id = Column(String(10), primary_key=True, comment="e.g., 2023-24")
    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=False)
    regular_season_games = Column(Integer, default=82)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    games = relationship("Game", back_populates="season", cascade="all, delete-orphan")
    player_stats = relationship("PlayerSeasonStats", back_populates="season", cascade="all, delete-orphan")
    team_stats = relationship("TeamSeasonStats", back_populates="season", cascade="all, delete-orphan")
    playoff_series = relationship("PlayoffSeries", back_populates="season", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Season(id='{self.season_id}')>"
