"""Game model"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Game(Base):
    """Game model"""
    __tablename__ = "games"

    game_id = Column(Integer, primary_key=True)
    season_id = Column(String(10), ForeignKey("seasons.season_id"), nullable=False, index=True)
    game_date = Column(Date, nullable=False, index=True)
    home_team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    game_type = Column(String(20), nullable=False, default="Regular Season", index=True,
                      comment="Regular Season / Playoffs / Finals")
    playoff_round = Column(String(50), nullable=True,
                          comment="First Round, Conference Semis, Conference Finals, Finals")
    arena = Column(String(200), nullable=True)
    attendance = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    season = relationship("Season", back_populates="games")
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_games")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_games")
    player_stats = relationship("PlayerGameStats", back_populates="game", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Game(id={self.game_id}, date='{self.game_date}')>"
