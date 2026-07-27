"""Pydantic schemas for Player API"""
from pydantic import BaseModel
from typing import Optional
from datetime import date


class PlayerBase(BaseModel):
    player_id: int
    first_name: str
    last_name: str
    full_name: str


class PlayerDetail(PlayerBase):
    birth_date: Optional[date] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    position: Optional[str] = None
    country: Optional[str] = None
    draft_year: Optional[int] = None
    draft_round: Optional[int] = None
    draft_number: Optional[int] = None
    nba_years: Optional[int] = None
    active: bool = False

    model_config = {"from_attributes": True}


class PlayerListResponse(BaseModel):
    total: int
    players: list[PlayerBase]


class PlayerSeasonStats(BaseModel):
    season_id: str
    team_id: int
    games_played: Optional[int] = None
    minutes_per_game: Optional[float] = None
    points_per_game: Optional[float] = None
    rebounds_per_game: Optional[float] = None
    assists_per_game: Optional[float] = None
    steals_per_game: Optional[float] = None
    blocks_per_game: Optional[float] = None
    field_goal_pct: Optional[float] = None
    three_point_pct: Optional[float] = None
    free_throw_pct: Optional[float] = None
    # Advanced stats
    player_efficiency_rating: Optional[float] = None
    true_shooting_pct: Optional[float] = None
    usage_rate: Optional[float] = None
    win_shares: Optional[float] = None
    box_plus_minus: Optional[float] = None
    value_over_replacement_player: Optional[float] = None

    model_config = {"from_attributes": True}


class PlayerCareerResponse(BaseModel):
    player: PlayerDetail
    seasons: list[PlayerSeasonStats]
