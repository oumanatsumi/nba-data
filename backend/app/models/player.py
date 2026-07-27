"""Player model"""
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Player(Base):
    """Player model"""
    __tablename__ = "players"

    player_id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    full_name = Column(String(200), nullable=False, index=True)
    birth_date = Column(Date, nullable=True)
    height_cm = Column(Integer, nullable=True)
    weight_kg = Column(Integer, nullable=True)
    position = Column(String(10), nullable=True)
    country = Column(String(100), nullable=True)
    draft_year = Column(Integer, nullable=True)
    draft_round = Column(Integer, nullable=True)
    draft_number = Column(Integer, nullable=True)
    nba_years = Column(Integer, nullable=True, comment="Years in NBA")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    season_stats = relationship("PlayerSeasonStats", back_populates="player", cascade="all, delete-orphan")
    game_stats = relationship("PlayerGameStats", back_populates="player", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Player(id={self.player_id}, name='{self.full_name}')>"
