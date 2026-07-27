"""Statistics models"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class PlayerGameStats(Base):
    """Player game statistics"""
    __tablename__ = "player_game_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("games.game_id", ondelete="CASCADE"), nullable=False, index=True)
    player_id = Column(Integer, ForeignKey("players.player_id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    is_starter = Column(Boolean, default=False)
    minutes_played = Column(Numeric(5, 2), nullable=True)

    # Basic stats
    points = Column(Integer, nullable=True)
    rebounds_total = Column(Integer, nullable=True)
    rebounds_offensive = Column(Integer, nullable=True)
    rebounds_defensive = Column(Integer, nullable=True)
    assists = Column(Integer, nullable=True)
    steals = Column(Integer, nullable=True)
    blocks = Column(Integer, nullable=True)
    turnovers = Column(Integer, nullable=True)
    personal_fouls = Column(Integer, nullable=True)

    # Shooting
    field_goals_made = Column(Integer, nullable=True)
    field_goals_attempted = Column(Integer, nullable=True)
    three_pointers_made = Column(Integer, nullable=True)
    three_pointers_attempted = Column(Integer, nullable=True)
    free_throws_made = Column(Integer, nullable=True)
    free_throws_attempted = Column(Integer, nullable=True)

    # Advanced stats
    plus_minus = Column(Integer, nullable=True)
    efficiency_rating = Column(Numeric(5, 2), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    game = relationship("Game", back_populates="player_stats")
    player = relationship("Player", back_populates="game_stats")

    __table_args__ = (
        UniqueConstraint('game_id', 'player_id', name='uq_player_game'),
    )

    def __repr__(self):
        return f"<PlayerGameStats(player_id={self.player_id}, game_id={self.game_id})>"


class PlayerSeasonStats(Base):
    """Player season statistics"""
    __tablename__ = "player_season_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    season_id = Column(String(10), ForeignKey("seasons.season_id"), nullable=False, index=True)
    player_id = Column(Integer, ForeignKey("players.player_id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)

    games_played = Column(Integer, nullable=True)
    games_started = Column(Integer, nullable=True)
    minutes_per_game = Column(Numeric(5, 2), nullable=True)

    # Basic stats (per game)
    points_per_game = Column(Numeric(5, 2), nullable=True)
    rebounds_per_game = Column(Numeric(5, 2), nullable=True)
    assists_per_game = Column(Numeric(5, 2), nullable=True)
    steals_per_game = Column(Numeric(5, 2), nullable=True)
    blocks_per_game = Column(Numeric(5, 2), nullable=True)
    turnovers_per_game = Column(Numeric(5, 2), nullable=True)

    # Shooting efficiency
    field_goal_pct = Column(Numeric(5, 4), nullable=True)
    three_point_pct = Column(Numeric(5, 4), nullable=True)
    free_throw_pct = Column(Numeric(5, 4), nullable=True)

    # Advanced stats
    player_efficiency_rating = Column(Numeric(5, 2), nullable=True, comment="PER")
    true_shooting_pct = Column(Numeric(5, 4), nullable=True, comment="TS%")
    usage_rate = Column(Numeric(5, 4), nullable=True, comment="USG%")
    offensive_rating = Column(Numeric(5, 2), nullable=True, comment="ORtg")
    defensive_rating = Column(Numeric(5, 2), nullable=True, comment="DRtg")
    win_shares = Column(Numeric(5, 2), nullable=True)
    box_plus_minus = Column(Numeric(5, 2), nullable=True)
    value_over_replacement_player = Column(Numeric(5, 2), nullable=True, comment="VORP")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    season = relationship("Season", back_populates="player_stats")
    player = relationship("Player", back_populates="season_stats")

    __table_args__ = (
        UniqueConstraint('season_id', 'player_id', 'team_id', name='uq_season_player_team'),
    )

    def __repr__(self):
        return f"<PlayerSeasonStats(player_id={self.player_id}, season='{self.season_id}')>"


class TeamSeasonStats(Base):
    """Team season statistics"""
    __tablename__ = "team_season_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    season_id = Column(String(10), ForeignKey("seasons.season_id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False, index=True)

    wins = Column(Integer, nullable=True)
    losses = Column(Integer, nullable=True)
    win_pct = Column(Numeric(5, 4), nullable=True)
    points_per_game = Column(Numeric(5, 2), nullable=True)
    points_allowed_per_game = Column(Numeric(5, 2), nullable=True)

    # Shooting
    field_goal_pct = Column(Numeric(5, 4), nullable=True)
    three_point_pct = Column(Numeric(5, 4), nullable=True)
    free_throw_pct = Column(Numeric(5, 4), nullable=True)

    # Other
    rebounds_per_game = Column(Numeric(5, 2), nullable=True)
    assists_per_game = Column(Numeric(5, 2), nullable=True)
    steals_per_game = Column(Numeric(5, 2), nullable=True)
    blocks_per_game = Column(Numeric(5, 2), nullable=True)

    # Rankings
    conference_rank = Column(Integer, nullable=True)
    division_rank = Column(Integer, nullable=True)
    playoff_seed = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    season = relationship("Season", back_populates="team_stats")
    team = relationship("Team", back_populates="season_stats")

    __table_args__ = (
        UniqueConstraint('season_id', 'team_id', name='uq_season_team'),
    )

    def __repr__(self):
        return f"<TeamSeasonStats(team_id={self.team_id}, season='{self.season_id}')>"
