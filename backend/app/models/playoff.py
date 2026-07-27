"""Playoff models"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class PlayoffSeries(Base):
    """Playoff series"""
    __tablename__ = "playoff_series"

    id = Column(Integer, primary_key=True, autoincrement=True)
    season_id = Column(String(10), ForeignKey("seasons.season_id"), nullable=False, index=True)
    round = Column(String(50), nullable=False, comment="First Round, Conference Semis, Conference Finals, Finals")
    series_number = Column(Integer, nullable=False)
    home_team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    home_team_wins = Column(Integer, nullable=True)
    away_team_wins = Column(Integer, nullable=True)
    winner_team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    season = relationship("Season", back_populates="playoff_series")

    __table_args__ = (
        UniqueConstraint('season_id', 'round', 'series_number', name='uq_season_round_series'),
    )

    def __repr__(self):
        return f"<PlayoffSeries(season='{self.season_id}', round='{self.round}')>"
