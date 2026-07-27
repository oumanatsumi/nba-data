"""Pydantic schemas for Team API"""
from pydantic import BaseModel
from typing import Optional


class TeamBase(BaseModel):
    team_id: int
    abbreviation: str
    nickname: str
    full_name: str
    city: Optional[str] = None
    conference: Optional[str] = None
    division: Optional[str] = None
    is_active: bool = True

    model_config = {"from_attributes": True}


class TeamSeasonStats(BaseModel):
    season_id: str
    wins: Optional[int] = None
    losses: Optional[int] = None
    win_pct: Optional[float] = None
    points_per_game: Optional[float] = None
    points_allowed_per_game: Optional[float] = None
    conference_rank: Optional[int] = None
    playoff_seed: Optional[int] = None

    model_config = {"from_attributes": True}


class TeamRoster(BaseModel):
    player_id: int
    full_name: str
    position: Optional[str] = None
    points_per_game: Optional[float] = None
    rebounds_per_game: Optional[float] = None
    assists_per_game: Optional[float] = None

    model_config = {"from_attributes": True}
